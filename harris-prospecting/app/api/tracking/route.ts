import { NextRequest, NextResponse } from 'next/server'
import { TrackingRecord } from '@/types'

// In-memory store for this demo. For production, replace with Vercel Postgres:
// import { sql } from '@vercel/postgres'
// and swap these functions for SQL queries.
const store: Map<string, TrackingRecord> = new Map()

export async function GET() {
  const records = Array.from(store.values()).sort(
    (a, b) => new Date(b.added).getTime() - new Date(a.added).getTime()
  )
  return NextResponse.json({ records })
}

export async function POST(req: NextRequest) {
  try {
    const records: TrackingRecord[] = await req.json()
    let added = 0
    records.forEach((r) => {
      if (!store.has(r.email)) {
        store.set(r.email, r)
        added++
      }
    })
    return NextResponse.json({ added, total: store.size })
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Unknown error'
    return NextResponse.json({ error: message }, { status: 500 })
  }
}

export async function PATCH(req: NextRequest) {
  try {
    const { email, field, value } = await req.json()
    const record = store.get(email)
    if (!record) return NextResponse.json({ error: 'Not found' }, { status: 404 })
    ;(record as unknown as Record<string, unknown>)[field] = value
    store.set(email, record)
    return NextResponse.json({ record })
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Unknown error'
    return NextResponse.json({ error: message }, { status: 500 })
  }
}

export async function DELETE() {
  store.clear()
  return NextResponse.json({ cleared: true })
}
