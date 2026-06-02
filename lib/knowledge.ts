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
    'Harris Computer builds and operates vertical-market software for municipal and local government — ERP and financial management, plus a municipal website & citizen-engagement platform. Trusted by tens of thousands of government organizations across North America.',
  motion: 'Founder/seller-led outbound + content. Long sales cycles, budget-driven, relationship-heavy.',
}

export const PRODUCTS: Product[] = [
  {
    key: 'Spectrum',
    name: 'Spectrum (ERP)',
    oneLiner: 'Enterprise ERP — finance, budgeting, HR and payroll for local government.',
    buyers: ['Finance Director', 'Town Clerk', 'Town Manager', 'Utility Billing Manager'],
    pain: 'Legacy ERP causing reporting delays, manual reconciliation, and disconnected finance/HR modules.',
  },
  {
    key: 'TRIO',
    name: 'TRIO (ERP)',
    oneLiner: 'All-in-one ERP for small and mid-sized local governments.',
    buyers: ['Finance Director', 'Town Clerk', 'Town Manager', 'Utility Billing Manager'],
    pain: 'Aging, disconnected modules and manual processes that are hard to maintain and report from.',
  },
  {
    key: 'MSI',
    name: 'MSI (ERP)',
    oneLiner: 'Financial management ERP — accounting, billing and revenue.',
    buyers: ['Finance Director', 'Town Clerk', 'Town Manager', 'Utility Billing Manager'],
    pain: 'Disconnected finance/billing systems, manual batch processing, weak reporting and self-service.',
  },
  {
    key: 'LocaleOne',
    name: 'LocaleOne (Municipal Website Platform)',
    oneLiner: 'Municipal website & citizen-engagement platform — CMS, online services and payments.',
    buyers: ['Finance Director', 'Town Manager', 'City Clerk', 'IT Director'],
    pain: 'Outdated, hard-to-update website; poor accessibility (ADA / Section 508) and mobile; no online services or payments; siloed from back-office systems.',
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
