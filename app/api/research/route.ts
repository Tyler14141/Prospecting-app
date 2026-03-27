import { NextRequest, NextResponse } from 'next/server'
import { anthropic, extractJSON } from '@/lib/anthropic'
import { Company } from '@/types'

const BATCH_SIZE = 25

export async function POST(req: NextRequest) {
  try {
    const { product, geo, size, pain, excludeCompanies = [] } = await req.json()

    const excludeBlock = excludeCompanies.length
      ? `\n\nDo NOT include any of these organizations (already in our pipeline):\n${excludeCompanies.join(', ')}`
      : ''

    // Find 100 orgs in batches of 25
    const allCompanies: Company[] = []
    const found: string[] = [...excludeCompanies]

    for (let batch = 0; batch < 4; batch++) {
      const alreadyFound = found.length
        ? `\n\nDo NOT include any of these organizations (already listed or in pipeline):\n${found.join(', ')}`
        : excludeBlock

      const prompt = `You are a B2B sales research assistant for Harris Computer, a large municipal government software company.

Find 25 real ${size} ${geo} that are strong prospects for Harris Computer's ${product} platform.

${product} solves: ${pain}

Use web search to find real organizations. Prioritize municipalities that have aging or legacy software systems and have not recently completed a major modernization.${alreadyFound}

Return ONLY a valid JSON array with no surrounding text or markdown:
[{"name":"City of Example","location":"Ontario, Canada","population":"28,000","website":"example.ca","why_fit":"One sentence fit rationale specific to ${product}."}]

Find exactly 25 real, distinct municipalities.`

      const response = await anthropic.messages.create({
        model: 'claude-sonnet-4-6',
        max_tokens: 8000,
        tools: [{ type: 'web_search_20250305' as const, name: 'web_search' }],
        messages: [{ role: 'user', content: prompt }],
      })

      const text = response.content
        .filter((b) => b.type === 'text')
        .map((b) => (b as { type: 'text'; text: string }).text)
        .join('\n')

      const companies = extractJSON<Company[]>(text)

      // Deduplicate against already found
      const existingNames = new Set(found.map((n) => n.toLowerCase()))
      const unique = companies.filter((c) => !existingNames.has(c.name.toLowerCase()))
      allCompanies.push(...unique)
      found.push(...unique.map((c) => c.name))
    }

    return NextResponse.json({ companies: allCompanies })
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Unknown error'
    return NextResponse.json({ error: message }, { status: 500 })
  }
}
