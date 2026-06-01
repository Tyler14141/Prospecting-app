import { NextRequest } from 'next/server'
import { anthropic, hasApiKey } from '@/lib/anthropic'
import { AGENTS, getAgent, type AgentDef } from '@/lib/agents'
import { KNOWLEDGE_VAULT } from '@/lib/knowledge'

export const runtime = 'nodejs'
export const maxDuration = 120

interface ChatBody {
  agentId: string
  messages: { role: 'user' | 'assistant'; content: string }[]
}

const WEB_SEARCH = { type: 'web_search_20260209', name: 'web_search' }

// system = shared Knowledge Vault (cached across all agents) + this agent's persona.
function systemFor(agent: AgentDef) {
  return [
    { type: 'text' as const, text: KNOWLEDGE_VAULT, cache_control: { type: 'ephemeral' as const } },
    { type: 'text' as const, text: agent.systemPersona },
  ]
}

// The CEO's delegation tool. Targets are every non-delegating agent.
const DELEGATE_TOOL = {
  name: 'delegate',
  description:
    'Delegate a concrete task to one of your specialist agents and stream their work back. ' +
    'Use this to actually produce content, research, outreach, account plans, or analysis ' +
    'instead of doing it yourself. Call it multiple times in one turn for parallel work.',
  input_schema: {
    type: 'object',
    properties: {
      agent_id: {
        type: 'string',
        enum: AGENTS.filter((a) => !a.canDelegate).map((a) => a.id),
        description: 'Which specialist to hand the task to.',
      },
      task: { type: 'string', description: 'A clear, self-contained instruction for the specialist.' },
    },
    required: ['agent_id', 'task'],
  },
}

export async function POST(req: NextRequest) {
  let body: ChatBody
  try {
    body = await req.json()
  } catch {
    return Response.json({ error: 'Invalid request body.' }, { status: 400 })
  }

  const agent = getAgent(body.agentId)
  if (!agent) return Response.json({ error: 'Unknown agent.' }, { status: 400 })
  if (!Array.isArray(body.messages) || body.messages.length === 0) {
    return Response.json({ error: 'No messages provided.' }, { status: 400 })
  }
  if (!hasApiKey()) {
    return Response.json(
      { error: 'ANTHROPIC_API_KEY is not set on the server. Add it to .env.local and restart.' },
      { status: 500 },
    )
  }

  const encoder = new TextEncoder()
  const stream = new ReadableStream<Uint8Array>({
    async start(controller) {
      const send = (s: string) => controller.enqueue(encoder.encode(s))
      try {
        if (agent.canDelegate) {
          await runOrchestrator(agent, body.messages, send)
        } else {
          await runAgent(agent, body.messages, send)
        }
      } catch (err) {
        send(`\n\n⚠️ ${err instanceof Error ? err.message : 'Unknown error'}`)
      } finally {
        controller.close()
      }
    },
  })

  return new Response(stream, {
    headers: { 'Content-Type': 'text/plain; charset=utf-8', 'Cache-Control': 'no-store' },
  })
}

// Stream a single agent turn — used both for specialists and non-delegating agents.
// Returns the full text the agent produced (so the CEO can use it as a tool result).
async function runAgent(
  agent: AgentDef,
  messages: unknown[],
  send: (s: string) => void,
  maxTokens = 4096,
): Promise<string> {
  const params: Record<string, unknown> = {
    model: agent.model,
    max_tokens: maxTokens,
    system: systemFor(agent),
    messages,
  }
  if (agent.thinking) params.thinking = { type: 'adaptive' }
  if (agent.webSearch) params.tools = [WEB_SEARCH]

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const run = anthropic.messages.stream(params as any)
  let acc = ''
  run.on('text', (delta: string) => {
    acc += delta
    send(delta)
  })
  await run.finalMessage()
  return acc
}

// The CEO loop: stream the CEO, run any delegated specialists, feed their work
// back, and repeat until the CEO is done (or we hit the delegation limit).
async function runOrchestrator(ceo: AgentDef, history: unknown[], send: (s: string) => void) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const convo: any[] = [...history]
  const tools = [DELEGATE_TOOL]

  for (let round = 0; round < 5; round++) {
    const params: Record<string, unknown> = {
      model: ceo.model,
      max_tokens: 4096,
      system: systemFor(ceo),
      messages: convo,
      tools,
    }
    if (ceo.thinking) params.thinking = { type: 'adaptive' }

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const run = anthropic.messages.stream(params as any)
    run.on('text', (delta: string) => send(delta))
    const final = await run.finalMessage()

    if (final.stop_reason !== 'tool_use') return

    // Preserve the assistant turn verbatim (includes thinking + tool_use blocks).
    convo.push({ role: 'assistant', content: final.content })

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const results: any[] = []
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    for (const block of final.content as any[]) {
      if (block.type !== 'tool_use' || block.name !== 'delegate') continue
      const agentId = String(block.input?.agent_id ?? '')
      const task = String(block.input?.task ?? '')
      const target = getAgent(agentId)

      if (!target || target.canDelegate) {
        results.push({
          type: 'tool_result',
          tool_use_id: block.id,
          content: `No such specialist: "${agentId}".`,
          is_error: true,
        })
        continue
      }

      const roleShort = target.role.split('·')[1]?.trim() ?? target.role
      send(`\n\n──────────\n▼ Delegated to ${target.name} · ${roleShort}\n   “${task}”\n\n`)
      const out = await runAgent(target, [{ role: 'user', content: task }], send, 1800)
      send(`\n\n▲ ${target.name} done — back to ${ceo.name}\n──────────\n\n`)

      results.push({
        type: 'tool_result',
        tool_use_id: block.id,
        content: out || '(the specialist returned no text)',
      })
    }

    if (results.length === 0) return
    convo.push({ role: 'user', content: results })
  }

  send('\n\n(Reached the delegation limit for this turn.)')
}
