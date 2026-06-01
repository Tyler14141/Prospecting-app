import { NextRequest } from 'next/server'
import { readVault, setVaultText } from '@/lib/store'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

export async function GET() {
  return Response.json(await readVault())
}

export async function PUT(req: NextRequest) {
  try {
    const { text } = await req.json()
    if (typeof text !== 'string') {
      return Response.json({ error: 'text (string) is required.' }, { status: 400 })
    }
    await setVaultText(text)
    return Response.json({ ok: true })
  } catch {
    return Response.json({ error: 'Invalid request.' }, { status: 400 })
  }
}
