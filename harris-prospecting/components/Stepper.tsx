'use client'

interface Step { label: string }
interface StepperProps { steps: Step[]; current: number }

export default function Stepper({ steps, current }: StepperProps) {
  return (
    <div style={{ display:'flex', position:'relative', marginBottom:'28px' }}>
      <div style={{ position:'absolute', top:'13px', left:'14px', right:'14px', height:'1px', background:'var(--border)', zIndex:0 }} />
      {steps.map((s, i) => {
        const n = i + 1
        const isActive = n === current
        const isDone = n < current
        return (
          <div key={n} style={{ flex:1, display:'flex', flexDirection:'column', alignItems:'center', gap:'5px', position:'relative', zIndex:1 }}>
            <div style={{
              width:'26px', height:'26px', borderRadius:'50%', display:'flex', alignItems:'center',
              justifyContent:'center', fontSize:'11px', fontWeight:600,
              background: isActive ? 'var(--text)' : isDone ? 'var(--green-bg)' : 'var(--bg-3)',
              border: `1.5px solid ${isActive ? 'var(--text)' : isDone ? '#16a34a' : 'var(--border-md)'}`,
              color: isActive ? '#fff' : isDone ? 'var(--green-text)' : 'var(--text-3)',
              transition: 'all 0.2s',
            }}>
              {isDone ? '✓' : n}
            </div>
            <div style={{
              fontSize:'11px', textAlign:'center',
              color: isActive ? 'var(--text)' : isDone ? 'var(--green-text)' : 'var(--text-3)',
              fontWeight: isActive ? 500 : 400,
            }}>
              {s.label}
            </div>
          </div>
        )
      })}
    </div>
  )
}
