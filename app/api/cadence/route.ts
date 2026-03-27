import { NextRequest, NextResponse } from 'next/server'
import { anthropic, extractJSON } from '@/lib/anthropic'
import { Cadence, OrgContacts } from '@/types'

const BATCH_SIZE = 10

export async function POST(req: NextRequest) {
  try {
    const { contacts, product, pain, sender, cal } = await req.json()

    const allContacts = (contacts as OrgContacts[]).flatMap((o) =>
      o.contacts.map((c) => ({ name: c.name, title: c.title, email: c.email, company: o.company }))
    )

    const calLine = cal ? `\n\nBooking link: ${cal}` : ''

    // Batch contacts to stay within token limits
    const allCadences: Cadence[] = []
    for (let i = 0; i < allContacts.length; i += BATCH_SIZE) {
      const batch = allContacts.slice(i, i + BATCH_SIZE)

      const prompt = `You are ${sender}, VP of Business Development at Harris Computer — a large established municipal government software company trusted by 50,000+ government organizations.

Write a 3-touch personalized cold email cadence for each contact below to book a 30-minute discovery call. Sound human and specific — reference the contact's actual org name and role. No generic openers.

Harris ${product} addresses: ${pain}

Touch 1 (Day 1): Value-led cold intro referencing their specific org. Max 130 words. End with a soft ask for a call.${calLine}
Touch 2 (Day 5): Follow-up with a new angle — peer municipality adoption, budget cycle pressure, compliance deadline, or role-specific operational pain. Max 100 words.
Touch 3 (Day 12): Short honest breakup email. Light CTA. Max 60 words.

Sign every email: ${sender}

Contacts: ${JSON.stringify(batch)}

Return ONLY a valid JSON array with no other text or markdown:
[{"contact_name":"Jane Smith","company":"City of Example","email":"jane.smith@example.ca","touches":[{"touch":1,"day":1,"subject":"Subject line","body":"Full email body"},{"touch":2,"day":5,"subject":"Subject line","body":"Full email body"},{"touch":3,"day":12,"subject":"Subject line","body":"Full email body"}]}]`

      const response = await anthropic.messages.create({
        model: 'claude-sonnet-4-6',
        max_tokens: 8000,
        messages: [{ role: 'user', content: prompt }],
      })

      const text = response.content
        .filter((b) => b.type === 'text')
        .map((b) => (b as { type: 'text'; text: string }).text)
        .join('\n')

      const cadences = extractJSON<Cadence[]>(text)
      allCadences.push(...cadences)
    }

    return NextResponse.json({ cadences: allCadences })
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Unknown error'
    return NextResponse.json({ error: message }, { status: 500 })
  }
}
