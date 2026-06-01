// Shared approve/reject logic, used by the Needs-Review UI, the content board,
// and email reply-to-approve. Approving an Email-channel draft with a recipient
// actually sends it (two-way email); otherwise the operator is notified.
import { updateContent, addActivity } from './store'
import { sendEmail, notifyOperator } from './email'
import type { ContentItem } from './pipeline'

export async function approveContent(id: string): Promise<ContentItem | null> {
  const item = await updateContent(id, { stage: 'approved' })
  if (!item) return null
  await addActivity({ type: 'review', message: `Approved: “${item.title}”` })
  if (item.channel === 'Email' && item.to) {
    const sent = await sendEmail({ to: item.to, subject: item.title, text: item.body })
    await addActivity({
      type: 'system',
      message: sent
        ? `Sent email to ${item.to}: “${item.title}”`
        : `Approved (send failed/disabled): “${item.title}”`,
    })
  } else {
    await notifyOperator(
      `Approved ${item.channel}: ${item.title}`,
      `${item.title} (${item.channel}${item.product ? ` · ${item.product}` : ''})\n\n${item.body}`,
    )
  }
  return item
}

export async function rejectContent(id: string): Promise<ContentItem | null> {
  const item = await updateContent(id, { stage: 'rejected' })
  if (item) await addActivity({ type: 'review', message: `Rejected: “${item.title}”` })
  return item
}
