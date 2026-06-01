// Shared agent execution: a tool loop for specialists and a delegation loop for
// the CEO. Used by the chat route (streaming), the workflow route, the inbound
// email route, and cron. Injects the editable Vault + team memory, logs
// activity, and tallies token usage.
import { anthropic } from './anthropic'
import { AGENTS, getAgent, type AgentDef } from './agents'
import { TOOL_DEFS, runTool } from './tools'
import { getVaultText, getMemoryText, addActivity } from './store'

const WEB_SEARCH = { type: 'web_search_20260209', name: 'web_search' }

export interface Usage {
  input: number
  output: number
}

function systemFor(agent: AgentDef, vaultText: string, memoryText: string) {
  const blocks = [
    { type: 'text' as const, text: vaultText, cache_control: { type: 'ephemeral' as const } },
    { type: 'text' as const, text: agent.systemPersona },
  ]
  if (memoryText) blocks.push({ type: 'text' as const, text: memoryText })
  if (agent.tools?.length) {
    blocks.push({
      type: 'text' as const,
      text: `You can call these tools to record real work: ${agent.tools.join(', ')}. Prefer calling them to actually save leads, create content for review, or remember durable facts, rather than only describing the result.`,
    })
  }
  return blocks
}

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

type Send = (s: string) => void

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function tally(usage: Usage, msg: any) {
  usage.input += msg?.usage?.input_tokens ?? 0
  usage.output += msg?.usage?.output_tokens ?? 0
}

// Entry point: branches between the CEO orchestrator and a plain specialist.
export async function runConversation(
  agent: AgentDef,
  messages: unknown[],
  send: Send,
): Promise<{ usage: Usage }> {
  const [vaultText, memoryText] = await Promise.all([getVaultText(), getMemoryText()])
  const usage: Usage = { input: 0, output: 0 }
  if (agent.canDelegate) await runOrchestrator(agent, messages, send, vaultText, memoryText, usage)
  else await runAgentTurn(agent, messages, send, vaultText, memoryText, usage)
  return { usage }
}

async function runAgentTurn(
  agent: AgentDef,
  messages: unknown[],
  send: Send,
  vaultText: string,
  memoryText: string,
  usage: Usage,
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
      system: systemFor(agent, vaultText, memoryText),
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
    tally(usage, final)

    if (final.stop_reason !== 'tool_use') break
    convo.push({ role: 'assistant', content: final.content })

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const results: any[] = []
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    for (const block of final.content as any[]) {
      if (block.type !== 'tool_use' || !TOOL_DEFS[block.name]) continue
      const note = await runTool(block.name, block.input ?? {}, agent.id)
      await addActivity({ agentId: agent.id, type: 'tool', message: note })
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

async function runOrchestrator(
  ceo: AgentDef,
  history: unknown[],
  send: Send,
  vaultText: string,
  memoryText: string,
  usage: Usage,
) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const convo: any[] = [...history]
  const tools = [DELEGATE_TOOL]

  for (let round = 0; round < 5; round++) {
    const params: Record<string, unknown> = {
      model: ceo.model,
      max_tokens: 4096,
      system: systemFor(ceo, vaultText, memoryText),
      messages: convo,
      tools,
    }
    if (ceo.thinking) params.thinking = { type: 'adaptive' }

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const run = anthropic.messages.stream(params as any)
    run.on('text', (delta: string) => send(delta))
    const final = await run.finalMessage()
    tally(usage, final)

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

      await addActivity({ agentId: 'ceo', type: 'delegate', message: `→ ${target.name}: ${task}` })
      const roleShort = target.role.split('·')[1]?.trim() ?? target.role
      send(`\n\n──────────\n▼ Delegated to ${target.name} · ${roleShort}\n   “${task}”\n\n`)
      const out = await runAgentTurn(
        target,
        [{ role: 'user', content: task }],
        send,
        vaultText,
        memoryText,
        usage,
        1800,
      )
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
