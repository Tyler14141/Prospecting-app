// Client-safe pipeline types & stage definitions. NO server imports here so it
// can be used from both the browser (app/page.tsx) and the server (lib/store.ts).

export const LEAD_STAGES = [
  { key: 'new', label: 'New' },
  { key: 'qualified', label: 'Qualified' },
  { key: 'contacted', label: 'Contacted' },
  { key: 'meeting', label: 'Meeting' },
  { key: 'won', label: 'Won' },
] as const
export type LeadStage = (typeof LEAD_STAGES)[number]['key']

export const CONTENT_STAGES = [
  { key: 'draft', label: 'Draft' },
  { key: 'review', label: 'Review' },
  { key: 'approved', label: 'Approved' },
  { key: 'published', label: 'Published' },
] as const
export type ContentStage = (typeof CONTENT_STAGES)[number]['key'] | 'rejected'

export const CONTENT_CHANNELS = ['LinkedIn', 'X', 'Email', 'Blog', 'Other'] as const

export interface Lead {
  id: string
  org: string
  location: string
  contact: string
  title: string
  email: string
  product: string
  whyFit: string
  stage: LeadStage
  createdAt: string
  crmId?: string // Salesforce record id once synced
  enriched?: boolean // contacts found via Matcha
}

export interface ContentItem {
  id: string
  title: string
  channel: string
  body: string
  product: string
  stage: ContentStage
  createdAt: string
  to?: string // prospect recipient (Email channel) — enables real send on approval
  leadId?: string // the lead this content is for, if any
}

export type ActivityType = 'tool' | 'delegate' | 'review' | 'workflow' | 'system'

export interface ActivityEvent {
  id: string
  ts: string
  agentId?: string
  type: ActivityType
  message: string
}

export interface MemoryNote {
  id: string
  ts: string
  agentId?: string
  text: string
}
