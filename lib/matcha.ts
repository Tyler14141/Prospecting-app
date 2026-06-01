// Matcha — your internal contact-enrichment tool. Pluggable: POSTs to
// MATCHA_API_URL with MATCHA_API_KEY and expects a list of contacts back.
// No-ops gracefully (returns []) when unconfigured.
export interface EnrichedContact {
  name: string
  title: string
  email: string
}

export function matchaConfigured(): boolean {
  return Boolean(process.env.MATCHA_API_URL)
}

export async function enrich(params: {
  org: string
  location?: string
  titles?: string[]
}): Promise<EnrichedContact[]> {
  const url = process.env.MATCHA_API_URL
  if (!url) return []
  const key = process.env.MATCHA_API_KEY
  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(key ? { Authorization: `Bearer ${key}` } : {}),
      },
      body: JSON.stringify(params),
    })
    if (!res.ok) return []
    const data = await res.json()
    // Accept {contacts:[...]} or a bare array; normalize the fields.
    const raw = Array.isArray(data) ? data : (data.contacts ?? [])
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    return (raw as any[])
      .map((c) => ({
        name: String(c.name ?? c.full_name ?? '').trim(),
        title: String(c.title ?? c.job_title ?? '').trim(),
        email: String(c.email ?? '').trim(),
      }))
      .filter((c) => c.name || c.email)
  } catch {
    return []
  }
}
