// Shared agent execution: a tool loop for specialists and a delegation loop for
// the CEO. Used by the chat route (streaming), the workflow route, the inbound
// email route, and cron. Injects the editable Vault + team memory, logs
// activity, and tallies token usage.
import { anthropic } from './anthropic'
import { AGENTS, getAgent, type AgentDef } from './agents'
import { TOOL_DEFS, runTool } from './tools'
import {
  getVaultText,
  getMemoryText,
  getInsightsText,
  getMaterialsText,
  getGoalsText,
  listAgentConfigs,
  addActivity,
} from './store'
import type { AgentOverride } from './pipeline'

const WEB_SEARCH = { type: 'web_search_20260209', name: 'web_search' }

export interface Usage {
  input: number
  output: number
}

interface Context {
  vault: string
  memory: string
  insights: string
  materials: string
  goals: string
  configs: Record<string, AgentOverride>
}

function charterText(a: AgentDef): string {
  const names = (ids?: string[]) => (ids ?? []).map((id) => getAgent(id)?.name ?? id).join(', ')
  const lines = [
    '# YOUR CHARTER',
    `Role: ${a.role}`,
    `Mission: ${a.mission}`,
    `You own: ${a.owns.join('; ')}`,
    `You are measured on: ${a.kpis.join('; ')}`,
  ]
  if (a.handoffFrom?.length) lines.push(`You receive work from: ${names(a.handoffFrom)}`)
  if (a.handoffTo?.length) lines.push(`You hand work off to: ${names(a.handoffTo)}`)
  return lines.join('\n')
}

function rosterText(): string {
  const specialists = AGENTS.filter((a) => !a.canDelegate)
  return `# YOUR TEAM (delegate by id)\n${specialists
    .map((a) => `- ${a.id}: ${a.name}, ${a.role} — ${a.mission}`)
    .join('\n')}`
}

function modelFor(agent: AgentDef, ctx: Context): string {
  return ctx.configs[agent.id]?.model || agent.model
}

function systemFor(agent: AgentDef, ctx: Context) {
  const o = ctx.configs[agent.id] ?? {}
  const blocks = [
    { type: 'text' as const, text: ctx.vault, cache_control: { type: 'ephemeral' as const } },
    { type: 'text' as const, text: charterText(agent) },
    { type: 'text' as const, text: agent.systemPersona },
  ]
  if (agent.canDelegate) blocks.push({ type: 'text' as const, text: rosterText() })
  if (o.jobDescription)
    blocks.push({
      type: 'text' as const,
      text: `# JOB DESCRIPTION (operator-set — authoritative for your role)\n${o.jobDescription}`,
    })
  if (o.context)
    blocks.push({ type: 'text' as const, text: `# ADDITIONAL CONTEXT (operator-provided)\n${o.context}` })
  if (o.instructions)
    blocks.push({
      type: 'text' as const,
      text: `# OPERATING INSTRUCTIONS (operator-set — follow these)\n${o.instructions}`,
    })
  if (ctx.goals) blocks.push({ type: 'text' as const, text: ctx.goals })
  if (ctx.materials) blocks.push({ type: 'text' as const, text: ctx.materials })
  if (ctx.insights) blocks.push({ type: 'text' as const, text: ctx.insights })
  if (ctx.memory) blocks.push({ type: 'text' as const, text: ctx.memory })
  const calendly = process.env.CALENDLY_URL
  if (calendly) {
    blocks.push({
      type: 'text' as const,
      text: `Booking link: when you propose a call or meeting, include this Calendly link so they can self-schedule: ${calendly}`,
    })
  }
  if (agent.tools?.length) {
    blocks.push({
      type: 'text' as const,
      text: `You can call these tools to record real work: ${agent.tools.join(', ')}. Prefer calling them to actually save/score leads, create content for review, or remember durable facts, rather than only describing the result.`,
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
  const [vault, memory, insights, materials, goals, configs] = await Promise.all([
    getVaultText(),
    getMemoryText(),
    getInsightsText(),
    getMaterialsText(),
    getGoalsText(),
    listAgentConfigs(),
  ])
  const ctx: Context = { vault, memory, insights, materials, goals, configs }
  const usage: Usage = { input: 0, output: 0 }
  if (agent.canDelegate) await runOrchestrator(agent, messages, send, ctx, usage)
  else await runAgentTurn(agent, messages, send, ctx, usage)
  return { usage }
}

async function runAgentTurn(
  agent: AgentDef,
  messages: unknown[],
  send: Send,
  ctx: Context,
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
      model: modelFor(agent, ctx),
      max_tokens: maxTokens,
      system: systemFor(agent, ctx),
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

async function runOrchestrator(ceo: AgentDef, history: unknown[], send: Send, ctx: Context, usage: Usage) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const convo: any[] = [...history]
  // The CEO can both delegate and use its own tools (e.g. set_goal).
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const tools: any[] = [DELEGATE_TOOL, ...(ceo.tools ?? []).map((n) => TOOL_DEFS[n]).filter(Boolean)]

  for (let round = 0; round < 5; round++) {
    const params: Record<string, unknown> = {
      model: modelFor(ceo, ctx),
      max_tokens: 4096,
      system: systemFor(ceo, ctx),
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
      if (block.type !== 'tool_use') continue
      // The CEO's own tools (e.g. set_goal) run directly.
      if (block.name !== 'delegate') {
        if (!TOOL_DEFS[block.name]) continue
        const note = await runTool(block.name, block.input ?? {}, ceo.id)
        await addActivity({ agentId: 'ceo', type: 'tool', message: note })
        send(`\n\n✓ ${note}\n`)
        results.push({ type: 'tool_result', tool_use_id: block.id, content: note })
        continue
      }
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
      const out = await runAgentTurn(target, [{ role: 'user', content: task }], send, ctx, usage, 1800)
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
