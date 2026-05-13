'use client'

export default function ErrorBox({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div style={{
      textAlign: 'center', padding: 32, color: 'var(--red-text)',
      background: 'var(--red-bg)', borderRadius: 10, border: '1px solid #fecaca',
    }}>
      <p style={{ fontSize: 14, marginBottom: 12 }}>{message}</p>
      <button onClick={onRetry} style={{
        padding: '5px 12px', fontSize: 12, fontWeight: 500, cursor: 'pointer',
        border: '1.5px solid var(--border-md)', borderRadius: 6,
        background: 'transparent', color: 'var(--text-2)', fontFamily: 'inherit',
      }}>Retry</button>
    </div>
  )
}
