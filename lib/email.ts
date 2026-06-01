// Minimal, dependency-free email sender. Uses Resend's HTTP API if configured
// (RESEND_API_KEY); otherwise it's a no-op that returns false so callers can
// degrade gracefully. Swap the fetch for any provider (Postmark, SendGrid, SES).
interface Mail {
  to: string
  subject: string
  text: string
}

export async function sendEmail(mail: Mail): Promise<boolean> {
  const key = process.env.RESEND_API_KEY
  const from = process.env.MAIL_FROM || 'Agentic OS <onboarding@resend.dev>'
  if (!key || !mail.to) return false
  try {
    const res = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: { Authorization: `Bearer ${key}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ from, to: mail.to, subject: mail.subject, text: mail.text }),
    })
    return res.ok
  } catch {
    return false
  }
}

// Notify the operator (you) — used to close the loop after async runs.
export async function notifyOperator(subject: string, text: string): Promise<boolean> {
  const to = process.env.OPERATOR_EMAIL
  if (!to) return false
  return sendEmail({ to, subject, text })
}

// Pull a bare address out of a "Name <email@host>" header value.
export function extractEmail(value: string): string {
  const m = value.match(/[^\s<>]+@[^\s<>]+/)
  return m ? m[0] : value.trim()
}
