// The Knowledge Vault — the shared business context every agent operates from.
// This is prepended (cached) to every agent's system prompt so the whole org
// reasons from one source of truth. Edit this to re-point the OS at a different
// company, product line, or ICP.

export interface Product {
  key: string
  name: string
  oneLiner: string
  buyers: string[]
  pain: string
}

export const COMPANY = {
  name: 'Harris Computer',
  tagline: 'Mission-critical software for the public sector.',
  description:
    'Harris Computer builds and operates vertical-market software for municipal and local government — ERP/finance, permitting & land management, tax & revenue, and utility billing. Trusted by tens of thousands of government organizations across North America.',
  motion: 'Founder/seller-led outbound + content. Long sales cycles, budget-driven, relationship-heavy.',
}

export const PRODUCTS: Product[] = [
  {
    key: 'Spectrum',
    name: 'Spectrum (ERP / Finance)',
    oneLiner: 'Government ERP for finance, budgeting, HR and payroll.',
    buyers: ['Finance Director', 'CFO', 'CAO / City Manager', 'Controller', 'IT Director'],
    pain: 'Legacy ERP causing reporting delays, manual reconciliation, and disconnected finance/HR modules.',
  },
  {
    key: 'TRIO',
    name: 'TRIO (Permitting & Land)',
    oneLiner: 'Permitting, inspections, code enforcement and land management.',
    buyers: ['Building Official', 'Director of Planning', 'City Clerk', 'Community Development Director'],
    pain: 'Paper-based permitting, no online applications, slow inspection scheduling, hard-to-track violations.',
  },
  {
    key: 'MSI',
    name: 'MSI (Tax & Revenue)',
    oneLiner: 'Tax billing, collections and revenue management.',
    buyers: ['City Treasurer', 'Tax Collector', 'Revenue Manager', 'Assessor', 'Finance Director'],
    pain: 'Disconnected tax billing/payment systems, manual batch processing, poor taxpayer self-service.',
  },
  {
    key: 'Aurora',
    name: 'Aurora (Utility Billing)',
    oneLiner: 'Utility billing and customer information system.',
    buyers: ['Utility Director', 'Public Works Director', 'Customer Service Manager', 'IT Director'],
    pain: 'Aging billing platform, high call volume from errors, no self-service portal, hard AMI integration.',
  },
]

export const ICP = {
  segment: 'US & Canadian municipalities, counties, and local government utilities.',
  size: 'Populations ~5k–250k; large enough to feel legacy-system pain, small enough to move without multi-year RFPs.',
  triggers: [
    'Aging or end-of-life legacy systems with no recent modernization',
    'Public budget cycle or grant funding window opening',
    'Compliance / reporting deadline pressure',
    'New finance, IT, or department leadership in the first 12 months',
  ],
}

// Rendered into a single block that gets prompt-cached across every agent call.
export const KNOWLEDGE_VAULT = `# KNOWLEDGE VAULT — ${COMPANY.name}

## Company
${COMPANY.description}
Tagline: ${COMPANY.tagline}
Growth motion: ${COMPANY.motion}

## Product lines
${PRODUCTS.map(
  (p) =>
    `- ${p.name}: ${p.oneLiner}\n  Buyers: ${p.buyers.join(', ')}\n  Pain it solves: ${p.pain}`,
).join('\n')}

## Ideal Customer Profile
- Segment: ${ICP.segment}
- Size: ${ICP.size}
- Buying triggers:
${ICP.triggers.map((t) => `  - ${t}`).join('\n')}

## Operating rules for every agent
- Ground all recommendations in the products and ICP above.
- Be specific and concrete; avoid generic marketing fluff.
- Municipal buyers are budget- and risk-conscious — lead with credibility and references, not hype.
- When you don't know a real-world fact, say so rather than inventing names, numbers, or quotes.`
