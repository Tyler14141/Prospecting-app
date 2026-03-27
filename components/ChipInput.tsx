'use client'
import { KeyboardEvent, useState } from 'react'

interface ChipInputProps {
  chips: string[]
  onChange: (chips: string[]) => void
}

export default function ChipInput({ chips, onChange }: ChipInputProps) {
  const [input, setInput] = useState('')

  const add = (val: string) => {
    const v = val.trim().replace(/,$/, '')
    if (v && !chips.includes(v)) onChange([...chips, v])
    setInput('')
  }

  const remove = (i: number) => onChange(chips.filter((_, idx) => idx !== i))

  const handleKey = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' || e.key === ',') { e.preventDefault(); add(input) }
    else if (e.key === 'Backspace' && input === '' && chips.length) remove(chips.length - 1)
  }

  return (
    <div
      style={{ border:'1.5px solid var(--border-md)', borderRadius:'var(--r-sm)', padding:'5px 7px', display:'flex', flexWrap:'wrap', gap:'4px', cursor:'text', minHeight:'72px', alignContent:'flex-start' }}
      onClick={() => document.getElementById('chip-inp')?.focus()}
    >
      {chips.map((c, i) => (
        <div key={i} style={{ background:'var(--bg-2)', border:'1px solid var(--border)', borderRadius:'4px', padding:'3px 7px', fontSize:'12px', display:'flex', alignItems:'center', gap:'4px' }}>
          <span>{c}</span>
          <span onClick={() => remove(i)} style={{ cursor:'pointer', color:'var(--text-3)', fontSize:'13px', lineHeight:1 }}>×</span>
        </div>
      ))}
      <input
        id="chip-inp"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKey}
        placeholder={chips.length === 0 ? 'Add a title…' : ''}
        style={{ border:'none', outline:'none', fontSize:'12px', fontFamily:'inherit', background:'transparent', minWidth:'110px', color:'var(--text)' }}
      />
    </div>
  )
}
