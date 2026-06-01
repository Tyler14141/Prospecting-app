import { NextRequest } from 'next/server'
import { hasApiKey } from '@/lib/anthropic'
import { getAgent } from '@/lib/agents'
import { getWorkflow } from '@/lib/workflows'
import { runConversation } from '@/lib/agentRunner'
import { addActivity } from '@/lib/store'

export const runtime = 'nodejs'
export const maxDuration = 120

export async function POST(req: NextRequest) {
  let id = ''
  try {
    id = String((await req.json()).id ?? '')
  } catch {
    return Response.json({ error: 'Invalid request.' }, { status: 400 })
  }

  const wf = getWorkflow(id)
  if (!wf) return Response.json({ error: 'Unknown workflow.' }, { status: 400 })
  const agent = getAgent(wf.agentId)
  if (!agent) return Response.json({ error: 'Unknown agent.' }, { status: 400 })
  if (!hasApiKey()) {
    return Response.json({ error: 'ANTHROPIC_API_KEY is not set on the server.' }, { status: 500 })
  }

  try {
    // Run to completion with a no-op sink; the agent's tools populate the boards.
    await runConversation(agent, [{ role: 'user', content: wf.prompt }], () => {})
    await addActivity({ agentId: agent.id, type: 'workflow', message: `Ran workflow: ${wf.name}` })
    return Response.json({ ok: true })
  } catch (err) {
    return Response.json(
      { error: err instanceof Error ? err.message : 'Workflow failed.' },
      { status: 500 },
    )
  }
}
