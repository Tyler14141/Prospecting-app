import { NextRequest } from 'next/server'
import { listAgentConfigs, setAgentConfig } from '@/lib/store'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

export async function GET() {
  return Response.json({ configs: await listAgentConfigs() })
}

export async function PUT(req: NextRequest) {
  try {
    const { agentId, patch } = await req.json()
    if (!agentId) return Response.json({ error: 'agentId is required.' }, { status: 400 })
    const config = await setAgentConfig(String(agentId), {
      jobDescription: patch?.jobDescription,
      context: patch?.context,
      instructions: patch?.instructions,
      model: patch?.model,
    })
    return Response.json({ config })
  } catch {
    return Response.json({ error: 'Invalid request.' }, { status: 400 })
  }
}
