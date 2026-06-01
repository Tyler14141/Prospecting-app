import { NextRequest } from 'next/server'
import { listLeads, updateLead } from '@/lib/store'

export const runtime = 'nodejs'

export async function GET() {
  return Response.json({ leads: await listLeads() })
}

export async function PATCH(req: NextRequest) {
  try {
    const { id, patch } = await req.json()
    const updated = await updateLead(String(id), patch ?? {})
    if (!updated) return Response.json({ error: 'Lead not found.' }, { status: 404 })
    return Response.json({ lead: updated })
  } catch {
    return Response.json({ error: 'Invalid request.' }, { status: 400 })
  }
}
