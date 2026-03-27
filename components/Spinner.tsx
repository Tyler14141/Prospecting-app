export default function Spinner({ label, sub }: { label: string; sub?: string }) {
  return (
    <div style={{ textAlign: 'center', padding: '48px 20px', color: 'var(--text-2)' }}>
      <div style={{
        width: 26, height: 26, border: '2.5px solid var(--border-md)',
        borderTopColor: 'var(--text)', borderRadius: '50%',
        animation: 'spin 0.65s linear infinite', margin: '0 auto 13px',
      }} />
      <style>{`@keyframes spin{to{transform:rotate(360deg)}}`}</style>
      <p style={{ fontSize: 14 }}>{label}</p>
      {sub && <small style={{ fontSize: 12, color: 'var(--text-3)', marginTop: 4, display: 'block' }}>{sub}</small>}
    </div>
  )
}
