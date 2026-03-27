import { NextRequest, NextResponse } from 'next/server'
import { anthropic, extractJSON } from '@/lib/anthropic'
import { OrgContacts } from '@/types'

const BATCH_SIZE = 5

export async function POST(req: NextRequest) {
  try {
    const { companies, titles, excludeEmails = [] } = await req.json()

    const excludeBlock = excludeEmails.length
      ? `\n\nDo NOT include contacts with any of these email addresses (already in our pipeline):\n${excludeEmails.join(', ')}`
      : ''

    // Process in batches of 5 orgs to stay within token limits
    const allContacts: OrgContacts[] = []
    for (let i = 0; i < companies.length; i += BATCH_SIZE) {
      const batch = companies.slice(i, i + BATCH_SIZE)

      const prompt = `You are a B2B sales research assistant. Municipal government websites publicly list staff names, titles, and email addresses in their staff directories or department pages.

For each municipality below, search their official website to find real staff contacts matching the target titles. Look for pages like /staff, /contact, /administration, /departments, /directory.

Municipalities: ${JSON.stringify(batch.map((c: { name: string; website: string }) => ({ name: c.name, website: c.website })))}

Target titles (find 3 per org — exact match or closest equivalent): ${titles.join(', ')}

Rules:
- If you find a real person on the website, mark source as "website" and use their exact name, title, and email.
- If you cannot find a real person for a title after searching, generate a realistic persona and mark source as "generated".
- Municipal email formats are typically: firstname.lastname@city.ca, flastname@cityname.gov, etc.
- Find exactly 3 contacts per organization.${excludeBlock}

Return ONLY a valid JSON array with no extra text:
[{"company":"City of Example","website":"example.ca","contacts":[{"name":"Jane Smith","title":"Finance Director","email":"jane.smith@example.ca","source":"website","profile_url":"https://example.ca/staff"},{"name":"Bob Jones","title":"IT Director","email":"bjones@example.ca","source":"generated","profile_url":""},{"name":"Alice Lee","title":"Controller","email":"alee@example.ca","source":"website","profile_url":"https://example.ca/staff"}]}]`

      const response = await anthropic.messages.create({
        model: 'claude-sonnet-4-6',
        max_tokens: 6000,
        tools: [{ type: 'web_search_20250305' as const, name: 'web_search' }],
        messages: [{ role: 'user', content: prompt }],
      })

      const text = response.content
        .filter((b) => b.type === 'text')
        .map((b) => (b as { type: 'text'; text: string }).text)
        .join('\n')

      const batchContacts = extractJSON<OrgContacts[]>(text)
      allContacts.push(...batchContacts)
    }

    // Server-side dedup: remove any contacts whose email is in the exclude list
    if (excludeEmails.length) {
      const excludeSet = new Set(excludeEmails.map((e: string) => e.toLowerCase()))
      for (const org of allContacts) {
        org.contacts = org.contacts.filter((c) => !excludeSet.has(c.email.toLowerCase()))
      }
    }

    return NextResponse.json({ contacts: allContacts })
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Unknown error'
    return NextResponse.json({ error: message }, { status: 500 })
  }
}
