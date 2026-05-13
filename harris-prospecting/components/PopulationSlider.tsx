'use client'
import { POP_LABELS } from '@/lib/constants'

interface PopulationSliderProps {
  minIdx: number
  maxIdx: number
  onMinChange: (v: number) => void
  onMaxChange: (v: number) => void
}

export default function PopulationSlider({ minIdx, maxIdx, onMinChange, onMaxChange }: PopulationSliderProps) {
  const pct = (v: number) => Math.round(v / 11 * 100)

  const handleMin = (v: number) => {
    if (v >= maxIdx) return
    onMinChange(v)
  }
  const handleMax = (v: number) => {
    if (v <= minIdx) return
    onMaxChange(v)
  }

  return (
    <div style={{ border:'1.5px solid var(--border-md)', borderRadius:'var(--r-sm)', padding:'12px 14px 10px' }}>
      <div style={{ display:'flex', justifyContent:'space-between', alignItems:'baseline', marginBottom:'10px' }}>
        <span style={{ fontSize:'13px', fontWeight:600 }}>{POP_LABELS[minIdx]}</span>
        <span style={{ fontSize:'11px', color:'var(--text-3)' }}>to</span>
        <span style={{ fontSize:'13px', fontWeight:600 }}>{POP_LABELS[maxIdx]}</span>
      </div>
      <div style={{ position:'relative', height:'20px', margin:'0 6px' }}>
        <div style={{ position:'absolute', top:'8px', left:0, right:0, height:'4px', background:'var(--bg-3)', borderRadius:'99px' }} />
        <div style={{ position:'absolute', top:'8px', height:'4px', background:'var(--text)', borderRadius:'99px', left:`${pct(minIdx)}%`, width:`${pct(maxIdx) - pct(minIdx)}%` }} />
        <input type="range" min={0} max={11} step={1} value={minIdx}
          onChange={(e) => handleMin(parseInt(e.target.value))}
          style={{ position:'absolute', width:'100%', top:0, left:0, background:'transparent', pointerEvents:'none', height:'20px' }} />
        <input type="range" min={0} max={11} step={1} value={maxIdx}
          onChange={(e) => handleMax(parseInt(e.target.value))}
          style={{ position:'absolute', width:'100%', top:0, left:0, background:'transparent', pointerEvents:'none', height:'20px' }} />
      </div>
      <div style={{ display:'flex', justifyContent:'space-between', marginTop:'8px' }}>
        {['1k','50k','250k','500k+'].map((l) => (
          <span key={l} style={{ fontSize:'10px', color:'var(--text-3)' }}>{l}</span>
        ))}
      </div>
    </div>
  )
}
