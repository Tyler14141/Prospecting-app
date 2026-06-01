import { NextRequest } from 'next/server'
import { listMaterials, addMaterial, deleteMaterial } from '@/lib/store'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

export async function GET() {
  return Response.json({ materials: await listMaterials() })
}

export async function POST(req: NextRequest) {
  try {
    const { product, title, body } = await req.json()
    if (!title || !body) {
      return Response.json({ error: 'title and body are required.' }, { status: 400 })
    }
    // Cap document size so a giant paste can't blow up the store / prompt.
    const material = await addMaterial({
      product: String(product || 'General'),
      title: String(title).slice(0, 200),
      body: String(body).slice(0, 20000),
    })
    return Response.json({ material })
  } catch {
    return Response.json({ error: 'Invalid request.' }, { status: 400 })
  }
}

export async function DELETE(req: NextRequest) {
  try {
    const { id } = await req.json()
    await deleteMaterial(String(id))
    return Response.json({ ok: true })
  } catch {
    return Response.json({ error: 'Invalid request.' }, { status: 400 })
  }
}
