import { NextRequest } from 'next/server'
import { listContent, updateContent } from '@/lib/store'
import { approveContent, rejectContent } from '@/lib/review'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

export async function GET() {
  return Response.json({ content: await listContent() })
}

export async function PATCH(req: NextRequest) {
  try {
    const { id, patch } = await req.json()
    const cid = String(id)

    // Approve/reject run the shared logic (incl. real send for outreach).
    if (patch?.stage === 'approved') {
      const item = await approveContent(cid)
      return item ? Response.json({ item }) : Response.json({ error: 'Not found.' }, { status: 404 })
    }
    if (patch?.stage === 'rejected') {
      const item = await rejectContent(cid)
      return item ? Response.json({ item }) : Response.json({ error: 'Not found.' }, { status: 404 })
    }

    const updated = await updateContent(cid, patch ?? {})
    if (!updated) return Response.json({ error: 'Content not found.' }, { status: 404 })
    return Response.json({ item: updated })
  } catch {
    return Response.json({ error: 'Invalid request.' }, { status: 400 })
  }
}
