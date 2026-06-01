import { NextRequest } from 'next/server'
import { anthropic, hasApiKey } from '@/lib/anthropic'
import { getAgent } from '@/lib/agents'
import { KNOWLEDGE_VAULT } from '@/lib/knowledge'

export const runtime = 'nodejs'
export const maxDuration = 60

interface ChatBody {
  agentId: string
  messages: { role: 'user' | 'assistant'; content: string }[]
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

  // system = shared Knowledge Vault (cached across all agents) + this agent's persona.
  const system = [
    { type: 'text' as const, text: KNOWLEDGE_VAULT, cache_control: { type: 'ephemeral' as const } },
    { type: 'text' as const, text: agent.systemPersona },
  ]

  // Brand-new model/tool string literals aren't in older SDK type defs; the
  // values are valid at the API layer, so we build the params object loosely.
  const params: Record<string, unknown> = {
    model: agent.model,
    max_tokens: 4096,
    system,
    messages: body.messages,
  }
  if (agent.thinking) params.thinking = { type: 'adaptive' }
  if (agent.webSearch) params.tools = [{ type: 'web_search_20260209', name: 'web_search' }]

  const encoder = new TextEncoder()
  const stream = new ReadableStream<Uint8Array>({
    async start(controller) {
      try {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const run = anthropic.messages.stream(params as any)
        run.on('text', (delta: string) => controller.enqueue(encoder.encode(delta)))
        await run.finalMessage()
        controller.close()
      } catch (err) {
        const msg = err instanceof Error ? err.message : 'Unknown error'
        controller.enqueue(encoder.encode(`\n\n⚠️ ${msg}`))
        controller.close()
      }
    },
  })

  return new Response(stream, {
    headers: { 'Content-Type': 'text/plain; charset=utf-8', 'Cache-Control': 'no-store' },
  })
}
