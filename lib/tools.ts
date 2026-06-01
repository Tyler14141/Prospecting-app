// Custom tools the agents can call to record real work. Server-only (writes to
// the store). The chat route maps an agent's `tools` names to these defs and
// executes calls via runTool().
import { addLead, addContent } from './store'

export interface ToolDef {
  name: string
  description: string
  input_schema: Record<string, unknown>
}

export const TOOL_DEFS: Record<string, ToolDef> = {
  save_lead: {
    name: 'save_lead',
    description:
      'Save a real, qualified prospect to the Lead Pipeline so the team can work it. ' +
      'Call this once per organization after you have identified a genuine fit — do not invent orgs.',
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
  create_content: {
    name: 'create_content',
    description:
      'Create a content or outreach draft and send it to the Content Pipeline for human review. ' +
      'Use for LinkedIn/X posts, emails, or other copy that the operator should approve before it ships.',
    input_schema: {
      type: 'object',
      properties: {
        title: { type: 'string', description: 'Short label for the draft' },
        channel: { type: 'string', enum: ['LinkedIn', 'X', 'Email', 'Blog', 'Other'] },
        body: { type: 'string', description: 'The full content, ready to ship' },
        product: { type: 'string', description: 'Related product, if any' },
      },
      required: ['title', 'channel', 'body'],
    },
  },
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export async function runTool(name: string, input: Record<string, any>): Promise<string> {
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
    return `Saved lead “${lead.org}”${lead.product ? ` (${lead.product})` : ''} to the Lead Pipeline.`
  }
  if (name === 'create_content') {
    const item = await addContent({
      title: String(input.title ?? 'Untitled'),
      channel: input.channel,
      body: String(input.body ?? ''),
      product: input.product,
    })
    return `Created ${item.channel} draft “${item.title}” — sent to Needs Review.`
  }
  return `Unknown tool: ${name}`
}
