export interface ICP {
  product: 'Spectrum' | 'TRIO' | 'MSI' | 'Aurora'
  geo: string
  size: string
  pain: string
  titles: string[]
  sender: string
  cal: string
}

export interface Company {
  name: string
  location: string
  population: string
  website: string
  why_fit: string
}

export interface Contact {
  name: string
  title: string
  email: string
  source: 'website' | 'generated'
  profile_url: string
}

export interface OrgContacts {
  company: string
  website: string
  contacts: Contact[]
}

export interface EmailTouch {
  touch: number
  day: number
  subject: string
  body: string
}

export interface Cadence {
  contact_name: string
  company: string
  email: string
  touches: EmailTouch[]
}

export type TrackingStatus = 'none' | 'sent' | 'opened' | 'replied' | 'booked'

export interface TrackingRecord {
  id: string
  name: string
  company: string
  email: string
  product: string
  status: TrackingStatus
  notes: string
  added: string
}
