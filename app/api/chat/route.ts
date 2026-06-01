import { NextRequest } from 'next/server'
import { anthropic, hasApiKey } from '@/lib/anthropic'
import { AGENTS, getAgent, type AgentDef } from '@/lib/agents'
import { KNOWLEDGE_VAULT } from '@/lib/knowledge'
import { TOOL_DEFS, runTool } from '@/lib/tools'

export const runtime = 'nodejs'
export const maxDuration = 120

interface ChatBody {
  agentId: string
  messages: { role: 'user' | 'assistant'; content: string }[]
}

const WEB_SEARCH = { type: 'web_search_20260209', name: 'web_search' }

// system = shared Knowledge Vault (cached across all agents) + this agent's
// persona + a nudge to actually use its tools.
function systemFor(agent: AgentDef) {
  const blocks = [
    { type: 'text' as const, text: KNOWLEDGE_VAULT, cache_control: { type: 'ephemeral' as const } },
    { type: 'text' as const, text: agent.systemPersona },
  ]
  if (agent.tools?.length) {
    blocks.push({
      type: 'text' as const,
      text: `You can call these tools to record real work: ${agent.tools.join(', ')}. Prefer calling them to actually save leads or create content for review, rather than only describing the result.`,
    })
  }
  return blocks
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

// Run a single agent as a tool loop: stream its text, execute any custom tool
// calls (save_lead / create_content) against the store, feed results back, and
// repeat until it's done. Returns the full text it produced.
async function runAgent(
  agent: AgentDef,
  messages: unknown[],
  send: (s: string) => void,
  maxTokens = 4096,
): Promise<string> {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const convo: any[] = [...messages]
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const tools: any[] = (agent.tools ?? []).map((n) => TOOL_DEFS[n]).filter(Boolean)
  if (agent.webSearch) tools.push(WEB_SEARCH)

  let text = ''
  for (let round = 0; round < 5; round++) {
    const params: Record<string, unknown> = {
      model: agent.model,
      max_tokens: maxTokens,
      system: systemFor(agent),
      messages: convo,
    }
    if (agent.thinking) params.thinking = { type: 'adaptive' }
    if (tools.length) params.tools = tools

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const run = anthropic.messages.stream(params as any)
    run.on('text', (delta: string) => {
      text += delta
      send(delta)
    })
    const final = await run.finalMessage()

    if (final.stop_reason !== 'tool_use') break
    convo.push({ role: 'assistant', content: final.content })

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const results: any[] = []
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    for (const block of final.content as any[]) {
      // Only custom tools need handling; server tools (web_search) resolve on their own.
      if (block.type !== 'tool_use' || !TOOL_DEFS[block.name]) continue
      const note = await runTool(block.name, block.input ?? {})
      const line = `\n\n✓ ${note}\n`
      text += line
      send(line)
      results.push({ type: 'tool_result', tool_use_id: block.id, content: note })
    }
    if (results.length === 0) break
    convo.push({ role: 'user', content: results })
  }
  return text
}

// The CEO loop: stream the CEO, run any delegated specialists (each with their
// own tools), feed their work back, and repeat until done.
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
