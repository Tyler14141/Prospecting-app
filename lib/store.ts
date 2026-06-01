// Tiny JSON-file datastore for leads & content. Good enough for local dev and
// demos; swap for Postgres/KV for production. Falls back to in-memory if the
// filesystem is read-only (e.g. serverless), so it never crashes.
import { promises as fs } from 'fs'
import path from 'path'
import type { Lead, ContentItem, LeadStage, ContentStage } from './pipeline'

interface DB {
  leads: Lead[]
  content: ContentItem[]
}

const FILE = path.join(process.cwd(), '.data', 'db.json')
let cache: DB | null = null

async function load(): Promise<DB> {
  if (cache) return cache
  try {
    const parsed = JSON.parse(await fs.readFile(FILE, 'utf8')) as Partial<DB>
    cache = { leads: parsed.leads ?? [], content: parsed.content ?? [] }
  } catch {
    cache = { leads: [], content: [] }
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
  }
  db.content.unshift(item)
  await persist(db)
  return item
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

export type { LeadStage, ContentStage }
