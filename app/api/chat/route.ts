import { NextRequest } from 'next/server'
import { hasApiKey } from '@/lib/anthropic'
import { getAgent } from '@/lib/agents'
import { runConversation } from '@/lib/agentRunner'

export const runtime = 'nodejs'
export const maxDuration = 120

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

  const encoder = new TextEncoder()
  const stream = new ReadableStream<Uint8Array>({
    async start(controller) {
      const send = (s: string) => controller.enqueue(encoder.encode(s))
      try {
        await runConversation(agent, body.messages, send)
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
