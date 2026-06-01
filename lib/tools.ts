// Custom tools the agents can call to do real work. Server-only. The agent
// runner maps an agent's `tools` names to these defs and executes via runTool().
import { addLead, addContent, addMemory, updateLead } from './store'
import { crmConfigured, pushLeadToSalesforce } from './salesforce'
import { enrich, matchaConfigured } from './matcha'

export interface ToolDef {
  name: string
  description: string
  input_schema: Record<string, unknown>
}

export const TOOL_DEFS: Record<string, ToolDef> = {
  save_lead: {
    name: 'save_lead',
    description:
      'Save a real, qualified prospect to the Lead Pipeline (and Salesforce, if connected). ' +
      'Call once per organization after you have identified a genuine fit — do not invent orgs.',
    input_schema: {
      type: 'object',
      properties: {
        org: { type: 'string', description: 'Organization / municipality name' },
        location: { type: 'string', description: 'City, state/province' },
        contact: { type: 'string', description: 'Contact full name, if known' },
        title: { type: 'string', description: 'Contact job title, if known' },
        email: { type: 'string', description: 'Contact email, if known' },
        product: { type: 'string', description: 'Best-fit product: Spectrum, TRIO, MSI, or Aurora' },
        why_fit: { type: 'string', description: 'One sentence on why they fit the ICP' },
      },
      required: ['org'],
    },
  },
  matcha: {
    name: 'matcha',
    description:
      'Enrich an organization with real decision-maker contacts (name, title, verified email) ' +
      'using Matcha, our internal contact tool. Call after save_lead with the lead_id to attach ' +
      'the best contact to that lead. Use this instead of guessing contact details.',
    input_schema: {
      type: 'object',
      properties: {
        org: { type: 'string', description: 'Organization to enrich' },
        location: { type: 'string', description: 'City, state/province (improves matching)' },
        titles: {
          type: 'array',
          items: { type: 'string' },
          description: 'Target job titles to look for (e.g. Finance Director, IT Director)',
        },
        lead_id: { type: 'string', description: 'The saved lead id to attach the contact to, if any' },
      },
      required: ['org'],
    },
  },
  create_content: {
    name: 'create_content',
    description:
      'Create a content or outreach draft and send it to the Content Pipeline for human review. ' +
      'Use for LinkedIn/X posts, emails, or other copy the operator should approve before it ships. ' +
      'For prospect outreach, set channel "Email" and include the recipient in "to" so it can be sent on approval.',
    input_schema: {
      type: 'object',
      properties: {
        title: { type: 'string', description: 'Short label for the draft' },
        channel: { type: 'string', enum: ['LinkedIn', 'X', 'Email', 'Blog', 'Other'] },
        body: { type: 'string', description: 'The full content, ready to ship' },
        product: { type: 'string', description: 'Related product, if any' },
        to: { type: 'string', description: 'Recipient email for Email-channel outreach' },
        lead_id: { type: 'string', description: 'The lead this content is for, if any' },
      },
      required: ['title', 'channel', 'body'],
    },
  },
  remember: {
    name: 'remember',
    description:
      'Save a durable note to the shared team memory — an operator preference, a decision, an ' +
      'account detail, or a fact worth recalling in future runs. Use sparingly.',
    input_schema: {
      type: 'object',
      properties: {
        note: { type: 'string', description: 'The fact or preference to remember, in one sentence.' },
      },
      required: ['note'],
    },
  },
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export async function runTool(name: string, input: Record<string, any>, agentId?: string): Promise<string> {
  if (name === 'save_lead') {
    const lead = await addLead({
      org: String(input.org ?? 'Unknown org'),
      location: input.location,
      contact: input.contact,
      title: input.title,
      email: input.email,
      product: input.product,
      whyFit: input.why_fit,
    })
    let crmNote = ''
    if (crmConfigured()) {
      const crmId = await pushLeadToSalesforce(lead)
      if (crmId) {
        await updateLead(lead.id, { crmId })
        crmNote = ' and synced to Salesforce'
      }
    }
    return `Saved lead “${lead.org}”${lead.product ? ` (${lead.product})` : ''}${crmNote} [id:${lead.id}].`
  }

  if (name === 'matcha') {
    const contacts = await enrich({
      org: String(input.org ?? ''),
      location: input.location,
      titles: Array.isArray(input.titles) ? input.titles.map(String) : undefined,
    })
    if (!contacts.length) {
      return matchaConfigured()
        ? `Matcha found no contacts for “${input.org}”. Try web search and save what you verify.`
        : `Matcha is not configured (set MATCHA_API_URL). Use web search to find a real contact, then save_lead.`
    }
    const best = contacts[0]
    if (input.lead_id) {
      await updateLead(String(input.lead_id), {
        contact: best.name || undefined,
        title: best.title || undefined,
        email: best.email || undefined,
        enriched: true,
      })
    }
    const list = contacts
      .slice(0, 4)
      .map((c) => `${c.name}${c.title ? `, ${c.title}` : ''}${c.email ? ` <${c.email}>` : ''}`)
      .join('; ')
    return `Matcha enriched “${input.org}”: ${list}.${input.lead_id ? ' Attached the top contact to the lead.' : ''}`
  }

  if (name === 'create_content') {
    const item = await addContent({
      title: String(input.title ?? 'Untitled'),
      channel: input.channel,
      body: String(input.body ?? ''),
      product: input.product,
      to: input.to,
      leadId: input.lead_id,
    })
    return `Created ${item.channel} draft “${item.title}”${item.to ? ` to ${item.to}` : ''} — sent to Needs Review.`
  }

  if (name === 'remember') {
    const note = String(input.note ?? '').trim()
    if (!note) return 'Nothing to remember.'
    await addMemory({ agentId, text: note })
    return `Saved to team memory: “${note.length > 80 ? note.slice(0, 80) + '…' : note}”`
  }

  return `Unknown tool: ${name}`
}
