import { NextRequest } from 'next/server'
import { listContent, updateContent, addActivity } from '@/lib/store'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

export async function GET() {
  return Response.json({ content: await listContent() })
}

export async function PATCH(req: NextRequest) {
  try {
    const { id, patch } = await req.json()
    const updated = await updateContent(String(id), patch ?? {})
    if (!updated) return Response.json({ error: 'Content not found.' }, { status: 404 })
    if (patch?.stage === 'approved' || patch?.stage === 'rejected') {
      await addActivity({
        type: 'review',
        message: `${patch.stage === 'approved' ? 'Approved' : 'Rejected'}: “${updated.title}”`,
      })
    }
    return Response.json({ item: updated })
  } catch {
    return Response.json({ error: 'Invalid request.' }, { status: 400 })
  }
}
