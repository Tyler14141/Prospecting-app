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
}

export interface ContentItem {
  id: string
  title: string
  channel: string
  body: string
  product: string
  stage: ContentStage
  createdAt: string
}
