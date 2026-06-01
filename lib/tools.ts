// Custom tools the agents can call to record real work. Server-only (writes to
// the store). The agent runner maps an agent's `tools` names to these defs and
// executes calls via runTool().
import { addLead, addContent, addMemory } from './store'

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
  remember: {
    name: 'remember',
    description:
      'Save a durable note to the shared team memory — an operator preference, a decision, an ' +
      'account detail, or a fact worth recalling in future runs. Use sparingly, for things that ' +
      'should persist beyond this conversation.',
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
  if (name === 'remember') {
    const note = String(input.note ?? '').trim()
    if (!note) return 'Nothing to remember.'
    await addMemory({ agentId, text: note })
    return `Saved to team memory: “${note.length > 80 ? note.slice(0, 80) + '…' : note}”`
  }
  return `Unknown tool: ${name}`
}
