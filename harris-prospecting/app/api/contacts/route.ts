import { NextRequest, NextResponse } from 'next/server'
import { anthropic, extractJSON } from '@/lib/anthropic'
import { OrgContacts } from '@/types'

export async function POST(req: NextRequest) {
  try {
    const { companies, titles } = await req.json()

    const prompt = `You are a B2B sales research assistant. Municipal government websites publicly list staff names, titles, and email addresses in their staff directories or department pages.

For each municipality below, search their official website to find real staff contacts matching the target titles. Look for pages like /staff, /contact, /administration, /departments, /directory.

Municipalities: ${JSON.stringify(companies.map((c: { name: string; website: string }) => ({ name: c.name, website: c.website })))}

Target titles (find 2 per org — exact match or closest equivalent): ${titles.join(', ')}

Rules:
- If you find a real person on the website, mark source as "website" and use their exact name, title, and email.
- If you cannot find a real person for a title after searching, generate a realistic persona and mark source as "generated".
- Municipal email formats are typically: firstname.lastname@city.ca, flastname@cityname.gov, etc.

Return ONLY a valid JSON array with no extra text:
[{"company":"City of Example","website":"example.ca","contacts":[{"name":"Jane Smith","title":"Finance Director","email":"jane.smith@example.ca","source":"website","profile_url":"https://example.ca/staff"},{"name":"Bob Jones","title":"IT Director","email":"bjones@example.ca","source":"generated","profile_url":""}]}]`

    const response = await anthropic.messages.create({
      model: 'claude-sonnet-4-6',
      max_tokens: 3000,
      tools: [{ type: 'web_search_20250305' as const, name: 'web_search' } as any],
      messages: [{ role: 'user', content: prompt }],
    })

    const text = response.content
      .filter((b) => b.type === 'text')
      .map((b) => (b as { type: 'text'; text: string }).text)
      .join('\n')

    const contacts = extractJSON<OrgContacts[]>(text)
    return NextResponse.json({ contacts })
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Unknown error'
    return NextResponse.json({ error: message }, { status: 500 })
  }
}
