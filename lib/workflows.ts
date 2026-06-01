// Predefined autonomous workflows. Client-safe (no server imports) so both the
// UI and the run endpoint can import it. Each workflow runs one agent with a
// fixed prompt; the agent's tools populate the pipelines.

export interface Workflow {
  id: string
  name: string
  agentId: string
  description: string
  prompt: string
}

export const WORKFLOWS: Workflow[] = [
  {
    id: 'scan-leads',
    name: 'Scan for new leads',
    agentId: 'researcher',
    description: 'Find and save 3 fresh ICP-fit prospects to the Lead Pipeline.',
    prompt:
      'Find 3 real municipalities that fit our ICP and look like strong prospects right now. ' +
      'For each qualified one, call save_lead with the best-fit product and a one-line reason. Keep it tight.',
  },
  {
    id: 'weekly-content',
    name: "Draft this week's content",
    agentId: 'cmo',
    description: 'Create 2 LinkedIn posts and send them to Needs Review.',
    prompt:
      'Write 2 distinct LinkedIn posts aimed at municipal buyers for our products. ' +
      'Call create_content once per post (channel "LinkedIn") to send each to the Content Pipeline for review.',
  },
  {
    id: 'follow-ups',
    name: 'Draft outbound follow-up',
    agentId: 'ae',
    description: 'Write a personalized follow-up email for review.',
    prompt:
      'Draft a short, personalized follow-up email for a municipal Finance Director evaluating Spectrum, ' +
      'and call create_content (channel "Email") to send it to the Content Pipeline for review.',
  },
  {
    id: 'scorecard',
    name: 'Weekly scorecard',
    agentId: 'analyst',
    description: 'Summarize pipeline health and the top next move.',
    prompt:
      'Give a short weekly scorecard of our pipeline health and the single highest-leverage next move ' +
      'for a typical week. Be concise and concrete.',
  },
]

export function getWorkflow(id: string): Workflow | undefined {
  return WORKFLOWS.find((w) => w.id === id)
}
