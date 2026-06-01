import { NextRequest } from 'next/server'
import { listLeads, updateLead } from '@/lib/store'
import { crmConfigured, pushLeadToSalesforce } from '@/lib/salesforce'
import { addActivity } from '@/lib/store'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

// POST {} → sync all not-yet-synced leads; POST {id} → sync one.
export async function POST(req: NextRequest) {
  if (!crmConfigured()) {
    return Response.json({ configured: false, synced: 0 })
  }
  let id: string | undefined
  try {
    id = (await req.json())?.id
  } catch {
    /* no body = sync all */
  }

  const leads = await listLeads()
  const targets = id ? leads.filter((l) => l.id === id) : leads.filter((l) => !l.crmId)

  let synced = 0
  for (const lead of targets) {
    const crmId = await pushLeadToSalesforce(lead)
    if (crmId) {
      await updateLead(lead.id, { crmId })
      synced++
    }
  }
  if (synced) await addActivity({ type: 'system', message: `Synced ${synced} lead(s) to Salesforce.` })
  return Response.json({ configured: true, synced })
}
