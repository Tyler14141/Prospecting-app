// Tiny JSON-file datastore for leads, content, activity, team memory, and the
// editable Knowledge Vault. Good enough for local dev and demos; swap for
// Postgres/KV for production. Falls back to in-memory if the FS is read-only.
import { promises as fs } from 'fs'
import path from 'path'
import { KNOWLEDGE_VAULT } from './knowledge'
import type {
  Lead,
  ContentItem,
  ActivityEvent,
  MemoryNote,
  Material,
  AgentOverride,
  LeadStage,
  ContentStage,
} from './pipeline'

interface DB {
  leads: Lead[]
  content: ContentItem[]
  activity: ActivityEvent[]
  memory: MemoryNote[]
  materials: Material[]
  agentConfig: Record<string, AgentOverride>
  vaultText?: string
}

const FILE = path.join(process.cwd(), '.data', 'db.json')
let cache: DB | null = null

async function load(): Promise<DB> {
  if (cache) return cache
  try {
    const parsed = JSON.parse(await fs.readFile(FILE, 'utf8')) as Partial<DB>
    cache = {
      leads: parsed.leads ?? [],
      content: parsed.content ?? [],
      activity: parsed.activity ?? [],
      memory: parsed.memory ?? [],
      materials: parsed.materials ?? [],
      agentConfig: parsed.agentConfig ?? {},
      vaultText: parsed.vaultText,
    }
  } catch {
    cache = { leads: [], content: [], activity: [], memory: [], materials: [], agentConfig: {} }
  }
  return cache
}

async function persist(db: DB) {
  cache = db
  try {
    await fs.mkdir(path.dirname(FILE), { recursive: true })
    await fs.writeFile(FILE, JSON.stringify(db, null, 2))
  } catch {
    // Read-only filesystem — keep changes in memory for this process.
  }
}

function uid(prefix: string) {
  return `${prefix}_${Date.now().toString(36)}${Math.random().toString(36).slice(2, 7)}`
}

/* ---------------- Leads ---------------- */

export async function listLeads(): Promise<Lead[]> {
  return (await load()).leads
}

export async function addLead(input: Partial<Lead> & { org: string }): Promise<Lead> {
  const db = await load()
  const lead: Lead = {
    id: uid('lead'),
    stage: input.stage ?? 'new',
    createdAt: new Date().toISOString(),
    org: input.org,
    location: input.location ?? '',
    contact: input.contact ?? '',
    title: input.title ?? '',
    email: input.email ?? '',
    product: input.product ?? '',
    whyFit: input.whyFit ?? '',
    crmId: input.crmId,
    enriched: input.enriched,
  }
  db.leads.unshift(lead)
  await persist(db)
  return lead
}

export async function updateLead(id: string, patch: Partial<Lead>): Promise<Lead | null> {
  const db = await load()
  const lead = db.leads.find((l) => l.id === id)
  if (!lead) return null
  Object.assign(lead, patch, { id: lead.id })
  await persist(db)
  return lead
}

export async function findLeadByEmail(email: string): Promise<Lead | null> {
  if (!email) return null
  const e = email.trim().toLowerCase()
  const db = await load()
  return db.leads.find((l) => l.email && l.email.toLowerCase() === e) ?? null
}

/* ---------------- Content ---------------- */

export async function listContent(): Promise<ContentItem[]> {
  return (await load()).content
}

export async function addContent(
  input: Partial<ContentItem> & { title: string; body: string },
): Promise<ContentItem> {
  const db = await load()
  const item: ContentItem = {
    id: uid('cnt'),
    stage: input.stage ?? 'review',
    createdAt: new Date().toISOString(),
    title: input.title,
    channel: input.channel ?? 'Other',
    body: input.body,
    product: input.product ?? '',
    to: input.to,
    leadId: input.leadId,
  }
  db.content.unshift(item)
  await persist(db)
  return item
}

export async function pendingReviewContent(): Promise<ContentItem[]> {
  return (await load()).content.filter((c) => c.stage === 'review')
}

export async function updateContent(
  id: string,
  patch: Partial<ContentItem>,
): Promise<ContentItem | null> {
  const db = await load()
  const item = db.content.find((c) => c.id === id)
  if (!item) return null
  Object.assign(item, patch, { id: item.id })
  await persist(db)
  return item
}

/* ---------------- Activity ---------------- */

export async function listActivity(): Promise<ActivityEvent[]> {
  return (await load()).activity
}

export async function addActivity(e: Omit<ActivityEvent, 'id' | 'ts'>): Promise<void> {
  const db = await load()
  db.activity.unshift({ id: uid('act'), ts: new Date().toISOString(), ...e })
  if (db.activity.length > 200) db.activity.length = 200
  await persist(db)
}

/* ---------------- Team memory ---------------- */

export async function listMemory(): Promise<MemoryNote[]> {
  return (await load()).memory
}

export async function addMemory(e: Omit<MemoryNote, 'id' | 'ts'>): Promise<void> {
  const db = await load()
  db.memory.unshift({ id: uid('mem'), ts: new Date().toISOString(), ...e })
  if (db.memory.length > 100) db.memory.length = 100
  await persist(db)
}

// Recent notes formatted for injection into an agent's system prompt.
export async function getMemoryText(): Promise<string> {
  const m = (await load()).memory
  if (!m.length) return ''
  const recent = m.slice(0, 12).map((n) => `- ${n.text}`).join('\n')
  return `# TEAM MEMORY (durable notes the team has saved — use when relevant)\n${recent}`
}

/* ---------------- Product materials ---------------- */

export async function listMaterials(): Promise<Material[]> {
  return (await load()).materials
}

export async function addMaterial(
  input: { product: string; title: string; body: string },
): Promise<Material> {
  const db = await load()
  const material: Material = {
    id: uid('mat'),
    createdAt: new Date().toISOString(),
    product: input.product || 'General',
    title: input.title,
    body: input.body,
  }
  db.materials.unshift(material)
  await persist(db)
  return material
}

export async function deleteMaterial(id: string): Promise<void> {
  const db = await load()
  db.materials = db.materials.filter((m) => m.id !== id)
  await persist(db)
}

// Operator-provided product docs, grouped per product, for injection into agent
// runs so messaging is grounded in real materials. Capped to keep prompts sane.
export async function getMaterialsText(): Promise<string> {
  const mats = (await load()).materials
  if (!mats.length) return ''
  const byProduct: Record<string, Material[]> = {}
  for (const m of mats) (byProduct[m.product] ??= []).push(m)
  const parts = Object.entries(byProduct).map(([product, list]) => {
    const items = list
      .map((m) => `### ${m.title}\n${m.body.length > 900 ? m.body.slice(0, 900) + '…' : m.body}`)
      .join('\n\n')
    return `## ${product}\n${items}`
  })
  let text = `# PRODUCT MATERIALS (operator-provided docs per product — ground all messaging in these when relevant)\n${parts.join('\n\n')}`
  if (text.length > 8000) text = text.slice(0, 8000) + '\n…(truncated)'
  return text
}

/* ---------------- Closed-loop insights ---------------- */

// A compact "what's working" summary, derived from outcomes, injected into
// every agent run so the team adapts targeting and messaging over time.
export async function getInsightsText(): Promise<string> {
  const db = await load()
  const leads = db.leads
  const content = db.content
  if (leads.length === 0 && content.length === 0) return ''

  const lines: string[] = []
  const total = leads.length
  const won = leads.filter((l) => l.stage === 'won').length
  const meeting = leads.filter((l) => l.stage === 'meeting' || l.stage === 'won').length
  if (total) {
    lines.push(`- Leads: ${total} total · ${won} won (${Math.round((won / total) * 100)}%) · ${meeting} reached a meeting`)
    // Win rate by product (only where we have signal)
    const byProduct: Record<string, { total: number; won: number }> = {}
    for (const l of leads) {
      const p = l.product || 'Unspecified'
      byProduct[p] ??= { total: 0, won: 0 }
      byProduct[p].total++
      if (l.stage === 'won') byProduct[p].won++
    }
    const top = Object.entries(byProduct)
      .sort((a, b) => b[1].won - a[1].won)
      .slice(0, 3)
      .map(([p, s]) => `${p} ${s.won}/${s.total}`)
      .join(', ')
    if (top) lines.push(`- By product (won/total): ${top}`)
  }
  const approved = content.filter((c) => c.stage === 'approved' || c.stage === 'published').length
  const rejected = content.filter((c) => c.stage === 'rejected').length
  const decided = approved + rejected
  if (decided) {
    lines.push(`- Content approval rate: ${Math.round((approved / decided) * 100)}% (${approved} approved, ${rejected} rejected)`)
  }
  if (!lines.length) return ''
  return `# WHAT'S WORKING (recent outcomes — use these to sharpen targeting and messaging)\n${lines.join('\n')}`
}

/* ---------------- Per-agent config overrides ---------------- */

export async function listAgentConfigs(): Promise<Record<string, AgentOverride>> {
  return (await load()).agentConfig
}

export async function getAgentConfig(id: string): Promise<AgentOverride> {
  return (await load()).agentConfig[id] ?? {}
}

export async function setAgentConfig(id: string, patch: AgentOverride): Promise<AgentOverride> {
  const db = await load()
  const next = { ...(db.agentConfig[id] ?? {}), ...patch }
  // Drop empty strings so they don't override the code defaults.
  ;(Object.keys(next) as (keyof AgentOverride)[]).forEach((k) => {
    if (next[k] === '' || next[k] == null) delete next[k]
  })
  db.agentConfig[id] = next
  await persist(db)
  return next
}

/* ---------------- Knowledge Vault ---------------- */

export async function getVaultText(): Promise<string> {
  return (await load()).vaultText ?? KNOWLEDGE_VAULT
}

export async function readVault(): Promise<{ text: string; isDefault: boolean }> {
  const db = await load()
  return { text: db.vaultText ?? KNOWLEDGE_VAULT, isDefault: db.vaultText == null }
}

export async function setVaultText(text: string): Promise<void> {
  const db = await load()
  db.vaultText = text
  await persist(db)
}

export type { LeadStage, ContentStage }
