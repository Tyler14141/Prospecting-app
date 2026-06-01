import { NextRequest } from 'next/server'
import { computeGoalProgress, addGoal, updateGoal, deleteGoal } from '@/lib/store'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

export async function GET() {
  return Response.json({ goals: await computeGoalProgress() })
}

export async function POST(req: NextRequest) {
  try {
    const { title, metric, target, owner, current } = await req.json()
    if (!title || !metric) {
      return Response.json({ error: 'title and metric are required.' }, { status: 400 })
    }
    const goal = await addGoal({
      title: String(title),
      metric: String(metric),
      target: Number(target) || 0,
      owner: owner ? String(owner) : undefined,
      current: current != null ? Number(current) : undefined,
    })
    return Response.json({ goal })
  } catch {
    return Response.json({ error: 'Invalid request.' }, { status: 400 })
  }
}

export async function PATCH(req: NextRequest) {
  try {
    const { id, patch } = await req.json()
    const goal = await updateGoal(String(id), patch ?? {})
    return goal ? Response.json({ goal }) : Response.json({ error: 'Not found.' }, { status: 404 })
  } catch {
    return Response.json({ error: 'Invalid request.' }, { status: 400 })
  }
}

export async function DELETE(req: NextRequest) {
  try {
    const { id } = await req.json()
    await deleteGoal(String(id))
    return Response.json({ ok: true })
  } catch {
    return Response.json({ error: 'Invalid request.' }, { status: 400 })
  }
}
