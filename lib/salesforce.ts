// Minimal Salesforce REST client. Token-based: set SALESFORCE_INSTANCE_URL and
// SALESFORCE_ACCESS_TOKEN (from a Connected App OAuth flow / session). No-ops
// gracefully when unconfigured so the rest of the app keeps working.
import type { Lead } from './pipeline'

const API_VERSION = 'v59.0'

export function crmConfigured(): boolean {
  return Boolean(process.env.SALESFORCE_INSTANCE_URL && process.env.SALESFORCE_ACCESS_TOKEN)
}

// Create (or note) a Salesforce Lead for one of our leads. Returns the SF id.
export async function pushLeadToSalesforce(lead: Lead): Promise<string | null> {
  const instance = process.env.SALESFORCE_INSTANCE_URL
  const token = process.env.SALESFORCE_ACCESS_TOKEN
  if (!instance || !token) return null

  // Salesforce Leads require Company + LastName.
  const [first, ...rest] = (lead.contact || '').trim().split(/\s+/)
  const lastName = rest.join(' ') || first || 'Unknown'
  const body = {
    Company: lead.org || 'Unknown',
    FirstName: rest.length ? first : undefined,
    LastName: lastName,
    Title: lead.title || undefined,
    Email: lead.email || undefined,
    City: lead.location || undefined,
    Description: lead.whyFit || undefined,
    LeadSource: 'Agentic OS',
  }

  try {
    const res = await fetch(`${instance}/services/data/${API_VERSION}/sobjects/Lead`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    if (!res.ok) return null
    const data = (await res.json()) as { id?: string }
    return data.id ?? null
  } catch {
    return null
  }
}
