'use client'
import { TrackedContact } from '@/lib/types'
import { STATUS_LABELS, STATUS_OPTS, StatusKey } from '@/lib/constants'

interface TrackingTableProps {
  tracking: TrackedContact[]
  onStatusChange: (id: string, status: StatusKey) => void
  onNoteChange: (id: string, notes: string) => void
  onClear: () => void
}

function Metric({ label, value, color, pct }: { label: string; value: number; color: string; pct: number }) {
  return (
    <div style={{ background:'var(--bg-2)', borderRadius:'var(--r-sm)', padding:'14px' }}>
      <div style={{ fontSize:'11px', color:'var(--text-3)', fontWeight:500, marginBottom:'5px' }}>{label}</div>
      <div style={{ fontSize:'26px', fontWeight:600, letterSpacing:'-0.5px', color }}>{value}</div>
      <div style={{ height:'3px', background:'var(--border)', borderRadius:'99px', marginTop:'6px', overflow:'hidden' }}>
        <div style={{ height:'100%', borderRadius:'99px', background:color, width:`${pct}%`, transition:'width 0.4s' }} />
      </div>
    </div>
  )
}

export function exportCSV(tracking: TrackedContact[]) {
  const header = 'Name,Company,Email,Product,Status,Notes,Added'
  const rows = tracking.map((t) =>
    [t.name, t.company, t.email, t.product, STATUS_LABELS[t.status], `"${t.notes.replace(/"/g,'""')}"`, t.added.slice(0,10)].join(',')
  )
  const csv = [header, ...rows].join('\n')
  const blob = new Blob([csv], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = 'harris-prospects.csv'; a.click()
  URL.revokeObjectURL(url)
}

export default function TrackingTable({ tracking, onStatusChange, onNoteChange, onClear }: TrackingTableProps) {
  const n = tracking.length
  const opened  = tracking.filter((t) => ['opened','replied','booked'].includes(t.status)).length
  const replied = tracking.filter((t) => ['replied','booked'].includes(t.status)).length
  const booked  = tracking.filter((t) => t.status === 'booked').length
  const pct = (v: number) => n ? Math.round(v / n * 100) : 0

  if (!n) return (
    <div style={{ textAlign:'center', padding:'52px 24px', color:'var(--text-3)' }}>
      <p style={{ fontSize:'14px', marginBottom:'6px', color:'var(--text-2)' }}>No contacts tracked yet</p>
      <small style={{ fontSize:'12px' }}>Complete the prospecting flow and click &ldquo;Add all contacts to tracking&rdquo;</small>
    </div>
  )

  return (
    <div>
      <div style={{ display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:'10px', marginBottom:'24px' }}>
        <Metric label="Contacts" value={n} color="var(--accent)" pct={100} />
        <Metric label="Opened" value={opened} color="var(--amber-text)" pct={pct(opened)} />
        <Metric label="Replied" value={replied} color="var(--green-text)" pct={pct(replied)} />
        <Metric label="Calls Booked" value={booked} color="var(--purple-text)" pct={pct(booked)} />
      </div>

      <div style={{ display:'flex', gap:'8px', justifyContent:'flex-end', marginBottom:'12px' }}>
        <button onClick={() => exportCSV(tracking)} style={{ display:'inline-flex', alignItems:'center', gap:'6px', padding:'7px 14px', borderRadius:'var(--r-sm)', fontSize:'12px', fontWeight:500, cursor:'pointer', border:'1.5px solid var(--border-md)', background:'transparent', color:'var(--text-2)', fontFamily:'inherit' }}>
          Export CSV
        </button>
        <button onClick={onClear} style={{ display:'inline-flex', alignItems:'center', gap:'6px', padding:'7px 14px', borderRadius:'var(--r-sm)', fontSize:'12px', fontWeight:500, cursor:'pointer', border:'1.5px solid var(--border-md)', background:'transparent', color:'var(--red-text)', fontFamily:'inherit' }}>
          Clear all
        </button>
      </div>

      <div style={{ overflowX:'auto' }}>
        <table style={{ width:'100%', borderCollapse:'collapse', fontSize:'13px' }}>
          <thead>
            <tr>
              {['Contact','Company','Product','Status','Notes','Added'].map((h) => (
                <th key={h} style={{ fontSize:'11px', fontWeight:600, color:'var(--text-3)', textTransform:'uppercase', letterSpacing:'0.05em', padding:'8px 12px', textAlign:'left', borderBottom:'1.5px solid var(--border)', background:'var(--bg-2)' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {tracking.map((t) => (
              <tr key={t.id} style={{ borderBottom:'1px solid var(--border)' }}>
                <td style={{ padding:'10px 12px' }}>
                  <div style={{ fontWeight:500 }}>{t.name}</div>
                  <div style={{ fontSize:'11px', color:'var(--accent-text)' }}>{t.email}</div>
                </td>
                <td style={{ padding:'10px 12px', fontSize:'13px' }}>{t.company}</td>
                <td style={{ padding:'10px 12px' }}>
                  <span style={{ display:'inline-flex', alignItems:'center', fontSize:'11px', padding:'2px 8px', borderRadius:'99px', background:'var(--bg-2)', color:'var(--text-2)', border:'1px solid var(--border)' }}>{t.product}</span>
                </td>
                <td style={{ padding:'10px 12px' }}>
                  <select
                    value={t.status}
                    onChange={(e) => onStatusChange(t.id, e.target.value as StatusKey)}
                    style={{ border:'1.5px solid var(--border-md)', borderRadius:'5px', padding:'4px 8px', fontSize:'12px', fontFamily:'inherit', background:'var(--bg)', color:'var(--text)', cursor:'pointer', outline:'none' }}
                  >
                    {STATUS_OPTS.map((s) => (
                      <option key={s} value={s}>{STATUS_LABELS[s]}</option>
                    ))}
                  </select>
                </td>
                <td style={{ padding:'10px 12px' }}>
                  <input
                    type="text"
                    defaultValue={t.notes}
                    onBlur={(e) => onNoteChange(t.id, e.target.value)}
                    placeholder="Add note…"
                    style={{ border:'1px solid var(--border)', borderRadius:'4px', padding:'4px 7px', fontSize:'12px', fontFamily:'inherit', width:'100%', minWidth:'120px', background:'var(--bg)', color:'var(--text)' }}
                  />
                </td>
                <td style={{ padding:'10px 12px', fontSize:'11px', color:'var(--text-3)', whiteSpace:'nowrap' }}>
                  {new Date(t.added).toLocaleDateString('en-CA', { month:'short', day:'numeric' })}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
