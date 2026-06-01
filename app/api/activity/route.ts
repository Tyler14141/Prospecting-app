import { listActivity } from '@/lib/store'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

export async function GET() {
  return Response.json({ activity: await listActivity() })
}
