'use client'
import { CA_REGIONS, US_REGIONS } from '@/lib/constants'

interface RegionPickerProps {
  country: 'CA' | 'US' | 'BOTH'
  selected: Set<string>
  onChange: (next: Set<string>) => void
}

export default function RegionPicker({ country, selected, onChange }: RegionPickerProps) {
  const groups = country === 'BOTH'
    ? [{ label: 'Canada', regions: CA_REGIONS }, { label: 'United States', regions: US_REGIONS }]
    : [{ label: null, regions: country === 'CA' ? CA_REGIONS : US_REGIONS }]

  const toggle = (code: string) => {
    const next = new Set(selected)
    next.has(code) ? next.delete(code) : next.add(code)
    onChange(next)
  }

  return (
    <div style={{ border:'1.5px solid var(--border-md)', borderRadius:'var(--r-sm)', padding:'8px', maxHeight:'130px', overflowY:'auto', display:'flex', flexWrap:'wrap', gap:'5px', alignContent:'flex-start' }}>
      {groups.map((g) => (
        <div key={g.label ?? 'single'} style={{ display:'contents' }}>
          {g.label && (
            <div style={{ fontSize:'10px', fontWeight:600, color:'var(--text-3)', textTransform:'uppercase', letterSpacing:'0.06em', width:'100%', marginTop:'4px' }}>
              {g.label}
            </div>
          )}
          {g.regions.map((r) => (
            <button
              key={r.code}
              onClick={() => toggle(r.code)}
              style={{
                fontSize:'11px', padding:'3px 9px', borderRadius:'99px', cursor:'pointer',
                border: `1.5px solid ${selected.has(r.code) ? 'var(--text)' : 'var(--border-md)'}`,
                background: selected.has(r.code) ? 'var(--text)' : 'var(--bg-2)',
                color: selected.has(r.code) ? '#fff' : 'var(--text-2)',
                transition:'all 0.12s', userSelect:'none', whiteSpace:'nowrap',
              }}
            >
              {r.name}
            </button>
          ))}
        </div>
      ))}
    </div>
  )
}
