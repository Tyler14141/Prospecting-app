import { NextRequest, NextResponse } from 'next/server'
import { anthropic, extractJSON } from '@/lib/anthropic'
import { Company } from '@/types'

export async function POST(req: NextRequest) {
  try {
    const { product, geo, size, pain } = await req.json()

    const prompt = `You are a B2B sales research assistant for Harris Computer, a large municipal government software company.

Find 6 real ${size} ${geo} that are strong prospects for Harris Computer's ${product} platform.

${product} solves: ${pain}

Use web search to find real organizations. Prioritize municipalities that have aging or legacy software systems and have not recently completed a major modernization.

Return ONLY a valid JSON array with no surrounding text or markdown:
[{"name":"City of Example","location":"Ontario, Canada","population":"28,000","website":"example.ca","why_fit":"One sentence fit rationale specific to ${product}."}]

Find exactly 6 real organizations.`

    const response = await anthropic.messages.create({
      model: 'claude-sonnet-4-6',
      max_tokens: 2000,
      tools: [{ type: 'web_search_20250305' as const, name: 'web_search' }],
      messages: [{ role: 'user', content: prompt }],
    })

    const text = response.content
      .filter((b) => b.type === 'text')
      .map((b) => (b as { type: 'text'; text: string }).text)
      .join('\n')

    const companies = extractJSON<Company[]>(text)
    return NextResponse.json({ companies })
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Unknown error'
    return NextResponse.json({ error: message }, { status: 500 })
  }
}
