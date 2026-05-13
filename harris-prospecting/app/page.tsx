'use client'
import { useState, useEffect } from 'react'
import Stepper from '@/components/Stepper'
import RegionPicker from '@/components/RegionPicker'
import PopulationSlider from '@/components/PopulationSlider'
import ChipInput from '@/components/ChipInput'
import TrackingTable from '@/components/TrackingTable'
import { PRODUCTS, ProductKey, POP_LABELS, CA_REGIONS, US_REGIONS } from '@/lib/constants'
import type { Company, OrgContacts, Cadence, TrackedContact } from '@/lib/types'
import type { StatusKey } from '@/lib/constants'

const STEPS = [
  { label: 'ICP Setup' },
  { label: 'Market Research' },
  { label: 'Real Contacts' },
  { label: 'Email Cadence' },
]
const AV = ['av-blue','av-green','av-amber','av-purple']

function initials(n: string) {
  return String(n||'').trim().split(/\s+/).slice(0,2).map((w)=>w[0]||'').join('').toUpperCase()
}
function esc(s: unknown) {
  return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;')
}

export default function Home() {
  const [tab, setTab] = useState<'agent'|'tracking'>('agent')
  const [step, setStep] = useState(1)

  // ICP state
  const [product, setProduct] = useState<ProductKey>('Spectrum')
  const [country, setCountry] = useState<'CA'|'US'|'BOTH'>('CA')
  const [selectedRegions, setSelectedRegions] = useState<Set<string>>(new Set(['ON']))
  const [minPop, setMinPop] = useState(0)
  const [maxPop, setMaxPop] = useState(11)
  const [titles, setTitles] = useState<string[]>(PRODUCTS.Spectrum.titles as unknown as string[])
  const [pain, setPain] = useState<string>(PRODUCTS.Spectrum.pain)
  const [sender, setSender] = useState('Tyler')
  const [cal, setCal] = useState('')

  // Results
  const [companies, setCompanies] = useState<Company[]>([])
  const [contacts, setContacts] = useState<OrgContacts[]>([])
  const [cadences, setCadences] = useState<Cadence[]>([])

  // UI state
  const [loading, setLoading] = useState(false)
  const [loadingMsg, setLoadingMsg] = useState('')
  const [error, setError] = useState('')
  const [openTouches, setOpenTouches] = useState<Set<string>>(new Set())

  // Tracking
  const [tracking, setTracking] = useState<TrackedContact[]>([])
  const [trackingPushed, setTrackingPushed] = useState(false)

  useEffect(() => {
    try { setTracking(JSON.parse(localStorage.getItem('harris_tracking')||'[]')) } catch {}
  }, [])

  const saveTracking = (t: TrackedContact[]) => {
    setTracking(t)
    try { localStorage.setItem('harris_tracking', JSON.stringify(t)) } catch {}
  }

  const onProductChange = (p: ProductKey) => {
    setProduct(p)
    setTitles([...PRODUCTS[p].titles])
    setPain(PRODUCTS[p].pain)
  }

  const onCountryChange = (c: 'CA'|'US'|'BOTH') => {
    setCountry(c)
    if (c === 'CA') setSelectedRegions(new Set(['ON']))
    else if (c === 'US') setSelectedRegions(new Set(['OH','MI','IN']))
    else setSelectedRegions(new Set(['ON','OH','MI']))
  }

  const getGeoString = () => {
    if (!selectedRegions.size) return country==='US' ? 'US municipalities' : country==='CA' ? 'Canadian municipalities' : 'North American municipalities'
    const allRegions = country==='BOTH' ? [...CA_REGIONS,...US_REGIONS] : country==='CA' ? CA_REGIONS : US_REGIONS
    const names = Array.from(selectedRegions).map((code) => allRegions.find((r)=>r.code===code)?.name || code)
    const lbl = country==='CA' ? 'Canada' : country==='US' ? 'the US' : 'Canada/US'
    return `municipalities in ${names.join(', ')} (${lbl})`
  }

  const getSizeString = () => {
    if (maxPop === 11) return `municipalities with population over ${POP_LABELS[minPop]}`
    return `municipalities with population between ${POP_LABELS[minPop]} and ${POP_LABELS[maxPop]}`
  }

  // ── API calls ──
  const doResearch = async () => {
    if (!titles.length) { alert('Add at least one target title.'); return }
    setLoading(true); setError(''); setStep(2)
    setLoadingMsg('Searching for real municipalities…')
    try {
      const res = await fetch('/api/research', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ product, geo: getGeoString(), size: getSizeString(), pain }),
      })
      const data = await res.json()
      if (data.error) throw new Error(data.error)
      setCompanies(data.companies)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Research failed')
    } finally { setLoading(false) }
  }

  const doContacts = async () => {
    setLoading(true); setError(''); setStep(3)
    setLoadingMsg('Searching municipal websites for staff directories…')
    try {
      const res = await fetch('/api/contacts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ companies, titles }),
      })
      const data = await res.json()
      if (data.error) throw new Error(data.error)
      setContacts(data.contacts)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Contact lookup failed')
    } finally { setLoading(false) }
  }

  const doCadence = async () => {
    setLoading(true); setError(''); setStep(4); setTrackingPushed(false)
    setLoadingMsg('Writing personalized 3-touch sequences…')
    try {
      const res = await fetch('/api/cadence', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ contacts, product, pain, sender, cal }),
      })
      const data = await res.json()
      if (data.error) throw new Error(data.error)
      setCadences(data.cadences)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Cadence generation failed')
    } finally { setLoading(false) }
  }

  const pushToTracking = () => {
    const existing = new Set(tracking.map((t) => t.email))
    const newContacts: TrackedContact[] = cadences
      .filter((c) => !existing.has(c.email))
      .map((c) => ({
        id: crypto.randomUUID(),
        name: c.contact_name, company: c.company, email: c.email,
        product, status: 'none', notes: '', added: new Date().toISOString(),
      }))
    saveTracking([...tracking, ...newContacts])
    setTrackingPushed(true)
  }

  const toggleTouch = (key: string) => {
    setOpenTouches((prev) => {
      const next = new Set(prev)
      next.has(key) ? next.delete(key) : next.add(key)
      return next
    })
  }

  const copyTouch = async (subject: string, body: string, btn: HTMLButtonElement) => {
    const text = `Subject: ${subject}\n\n${body}`
    try {
      await navigator.clipboard.writeText(text)
    } catch {
      const ta = document.createElement('textarea')
      ta.value = text; document.body.appendChild(ta); ta.select()
      document.execCommand('copy'); document.body.removeChild(ta)
    }
    btn.textContent = 'Copied!'
    setTimeout(() => { btn.textContent = 'Copy email' }, 1500)
  }

  // ── Shared styles ──
  const s = {
    field: { display:'flex' as const, flexDirection:'column' as const, gap:'5px' },
    label: { fontSize:'11px', fontWeight:600, color:'var(--text-3)', textTransform:'uppercase' as const, letterSpacing:'0.05em' },
    input: { border:'1.5px solid var(--border-md)', borderRadius:'var(--r-sm)', padding:'8px 11px', fontSize:'13px', background:'var(--bg)', color:'var(--text)', fontFamily:'inherit', outline:'none' } as React.CSSProperties,
    select: { border:'1.5px solid var(--border-md)', borderRadius:'var(--r-sm)', padding:'8px 11px', fontSize:'13px', background:'var(--bg)', color:'var(--text)', fontFamily:'inherit', outline:'none' } as React.CSSProperties,
    textarea: { border:'1.5px solid var(--border-md)', borderRadius:'var(--r-sm)', padding:'8px 11px', fontSize:'13px', background:'var(--bg)', color:'var(--text)', fontFamily:'inherit', outline:'none', resize:'vertical' as const, lineHeight:'1.55' },
    btnPrimary: { display:'inline-flex', alignItems:'center', gap:'6px', padding:'9px 16px', borderRadius:'var(--r-sm)', fontSize:'13px', fontWeight:500, cursor:'pointer', border:'1.5px solid var(--text)', background:'var(--text)', color:'#fff', fontFamily:'inherit' } as React.CSSProperties,
    btnGhost: { display:'inline-flex', alignItems:'center', gap:'6px', padding:'9px 16px', borderRadius:'var(--r-sm)', fontSize:'13px', fontWeight:500, cursor:'pointer', border:'1.5px solid var(--border-md)', background:'transparent', color:'var(--text-2)', fontFamily:'inherit' } as React.CSSProperties,
    btnGhostSm: { display:'inline-flex', alignItems:'center', gap:'6px', padding:'5px 10px', borderRadius:'var(--r-sm)', fontSize:'11px', fontWeight:500, cursor:'pointer', border:'1.5px solid var(--border-md)', background:'transparent', color:'var(--text-2)', fontFamily:'inherit' } as React.CSSProperties,
    card: { background:'var(--bg)', border:'1.5px solid var(--border)', borderRadius:'var(--r)', padding:'13px 15px' },
    tag: { display:'inline-flex', alignItems:'center', fontSize:'11px', padding:'2px 8px', borderRadius:'99px', background:'var(--bg-2)', color:'var(--text-2)', border:'1px solid var(--border)', whiteSpace:'nowrap' as const },
  }

  const TL = ['Intro','Follow-up','Breakup']
  const TB_STYLES = [
    { background:'var(--accent-bg)', color:'var(--accent-text)' },
    { background:'var(--green-bg)', color:'var(--green-text)' },
    { background:'var(--red-bg)', color:'var(--red-text)' },
  ]

  return (
    <div style={{ maxWidth:'900px', margin:'0 auto', padding:'32px 20px 60px' }}>
      {/* Header */}
      <div style={{ marginBottom:'28px' }}>
        <h1 style={{ fontSize:'20px', fontWeight:600, letterSpacing:'-0.3px' }}>Harris Prospecting Agent</h1>
        <p style={{ fontSize:'14px', color:'var(--text-2)', marginTop:'4px' }}>ICP research → real municipal contacts → personalized email cadences → outcome tracking</p>
      </div>

      {/* Tabs */}
      <div style={{ display:'flex', gap:'2px', marginBottom:'28px', borderBottom:'1.5px solid var(--border)' }}>
        {(['agent','tracking'] as const).map((t) => (
          <button key={t} onClick={() => setTab(t)} style={{ padding:'9px 16px', fontSize:'13px', fontWeight:500, cursor:'pointer', border:'none', background:'transparent', fontFamily:'inherit', borderBottom:`2px solid ${tab===t?'var(--text)':'transparent'}`, marginBottom:'-1.5px', color: tab===t?'var(--text)':'var(--text-3)', transition:'all 0.15s' }}>
            {t === 'agent' ? 'Prospecting Agent' : <>Tracking{tracking.length > 0 && <span style={{ display:'inline-flex', alignItems:'center', justifyContent:'center', minWidth:'18px', height:'18px', borderRadius:'99px', background:'var(--accent-bg)', color:'var(--accent-text)', fontSize:'10px', fontWeight:600, padding:'0 5px', marginLeft:'6px' }}>{tracking.length}</span>}</>}
          </button>
        ))}
      </div>

      {/* ── AGENT TAB ── */}
      {tab === 'agent' && (
        <div>
          <Stepper steps={STEPS} current={step} />

          {/* Step 1: ICP */}
          {step === 1 && (
            <div>
              <div style={{ marginBottom:'22px' }}>
                <h2 style={{ fontSize:'17px', fontWeight:600 }}>Configure your ICP</h2>
                <p style={{ fontSize:'13px', color:'var(--text-2)', marginTop:'3px' }}>Select the Harris product and define who you&apos;re targeting.</p>
              </div>
              <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:'18px', marginBottom:'24px' }}>
                <div style={{ display:'flex', flexDirection:'column', gap:'14px' }}>
                  <div style={s.field}>
                    <label style={s.label}>Harris Product</label>
                    <select style={s.select} value={product} onChange={(e) => onProductChange(e.target.value as ProductKey)}>
                      <option value="Spectrum">Spectrum — Municipal ERP &amp; Finance</option>
                      <option value="TRIO">TRIO — Permitting &amp; Code Enforcement</option>
                      <option value="MSI">MSI — Revenue &amp; Tax Management</option>
                      <option value="Aurora">Aurora — Utility Billing</option>
                    </select>
                  </div>
                  <div style={s.field}>
                    <label style={s.label}>Country</label>
                    <select style={s.select} value={country} onChange={(e) => onCountryChange(e.target.value as 'CA'|'US'|'BOTH')}>
                      <option value="CA">Canada</option>
                      <option value="US">United States</option>
                      <option value="BOTH">Canada + US</option>
                    </select>
                  </div>
                  <div style={s.field}>
                    <label style={s.label}>States / Provinces <span style={{ fontWeight:400, textTransform:'none', letterSpacing:0 }}>(click to toggle)</span></label>
                    <RegionPicker country={country} selected={selectedRegions} onChange={setSelectedRegions} />
                  </div>
                  <div style={s.field}>
                    <label style={s.label}>Population Range</label>
                    <PopulationSlider minIdx={minPop} maxIdx={maxPop} onMinChange={setMinPop} onMaxChange={setMaxPop} />
                  </div>
                  <div style={s.field}>
                    <label style={s.label}>Sender Name</label>
                    <input style={s.input} type="text" value={sender} onChange={(e) => setSender(e.target.value)} placeholder="Your first name" />
                  </div>
                  <div style={s.field}>
                    <label style={s.label}>Calendly / Booking Link</label>
                    <input style={s.input} type="text" value={cal} onChange={(e) => setCal(e.target.value)} placeholder="https://calendly.com/your-link" />
                  </div>
                </div>
                <div style={{ display:'flex', flexDirection:'column', gap:'14px' }}>
                  <div style={s.field}>
                    <label style={s.label}>Target Titles <span style={{ fontWeight:400, textTransform:'none', letterSpacing:0 }}>(Enter to add)</span></label>
                    <ChipInput chips={titles} onChange={setTitles} />
                  </div>
                  <div style={s.field}>
                    <label style={s.label}>Key Value Props / Pain Points</label>
                    <textarea style={{ ...s.textarea, height:'180px' }} value={pain} onChange={(e) => setPain(e.target.value)} />
                  </div>
                </div>
              </div>
              <button style={s.btnPrimary} onClick={doResearch}>Research market →</button>
            </div>
          )}

          {/* Loading state */}
          {loading && (
            <div style={{ textAlign:'center', padding:'48px 20px', color:'var(--text-2)' }}>
              <div style={{ width:'26px', height:'26px', border:'2.5px solid var(--border-md)', borderTopColor:'var(--text)', borderRadius:'50%', animation:'spin 0.65s linear infinite', margin:'0 auto 13px' }} />
              <p style={{ fontSize:'14px' }}>{loadingMsg}</p>
              <small style={{ fontSize:'12px', color:'var(--text-3)', marginTop:'4px', display:'block' }}>This may take 15–30 seconds</small>
              <style>{`@keyframes spin{to{transform:rotate(360deg)}}`}</style>
            </div>
          )}

          {/* Error state */}
          {!loading && error && (
            <div style={{ textAlign:'center', padding:'32px', color:'var(--red-text)', background:'var(--red-bg)', borderRadius:'var(--r)', border:'1px solid #fecaca', marginTop:'12px' }}>
              <p style={{ fontSize:'14px', marginBottom:'10px' }}>{error}</p>
              <button style={s.btnGhostSm} onClick={() => { setError(''); setStep(step) }}>← Back</button>
            </div>
          )}

          {/* Step 2: Companies */}
          {!loading && !error && step === 2 && companies.length > 0 && (
            <div>
              <div style={{ display:'flex', justifyContent:'space-between', alignItems:'flex-start', marginBottom:'18px' }}>
                <div>
                  <h2 style={{ fontSize:'17px', fontWeight:600 }}>Market Research</h2>
                  <p style={{ fontSize:'13px', color:'var(--text-2)', marginTop:'3px' }}>Found {companies.length} target organizations for {product}</p>
                </div>
                <button style={s.btnGhostSm} onClick={() => setStep(1)}>← Back</button>
              </div>
              <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fill,minmax(250px,1fr))', gap:'10px' }}>
                {companies.map((c, i) => (
                  <div key={i} style={s.card}>
                    <div style={{ fontSize:'14px', fontWeight:600, marginBottom:'2px' }}>{c.name}</div>
                    <div style={{ fontSize:'12px', color:'var(--text-2)', marginBottom:'8px' }}>{c.location} · {c.population} pop</div>
                    <div style={{ marginBottom:'7px' }}><span style={s.tag}>{c.website}</span></div>
                    <div style={{ fontSize:'12px', color:'var(--text-2)', lineHeight:'1.55', paddingTop:'9px', borderTop:'1px solid var(--border)' }}>{c.why_fit}</div>
                  </div>
                ))}
              </div>
              <div style={{ display:'flex', justifyContent:'flex-end', marginTop:'22px', paddingTop:'18px', borderTop:'1px solid var(--border)' }}>
                <button style={s.btnPrimary} onClick={doContacts}>Find real contacts →</button>
              </div>
            </div>
          )}

          {/* Step 3: Contacts */}
          {!loading && !error && step === 3 && contacts.length > 0 && (
            <div>
              <div style={{ display:'flex', justifyContent:'space-between', alignItems:'flex-start', marginBottom:'18px' }}>
                <div>
                  <h2 style={{ fontSize:'17px', fontWeight:600 }}>Real Contacts</h2>
                  <p style={{ fontSize:'13px', color:'var(--text-2)', marginTop:'3px' }}>
                    {contacts.reduce((s,o) => s + o.contacts.length, 0)} contacts —{' '}
                    {contacts.reduce((s,o) => s + o.contacts.filter((c) => c.source === 'website').length, 0)} sourced from municipal websites
                  </p>
                </div>
                <button style={s.btnGhostSm} onClick={() => setStep(2)}>← Back</button>
              </div>
              {contacts.map((org, oi) => (
                <div key={oi} style={{ marginBottom:'24px' }}>
                  <div style={{ fontSize:'11px', fontWeight:600, color:'var(--text-3)', textTransform:'uppercase', letterSpacing:'0.07em', marginBottom:'9px', paddingBottom:'5px', borderBottom:'1px solid var(--border)', display:'flex', alignItems:'center', gap:'8px' }}>
                    {org.company} <span style={s.tag}>{org.website}</span>
                  </div>
                  <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fill,minmax(250px,1fr))', gap:'10px' }}>
                    {org.contacts.map((c, ci) => (
                      <div key={ci} style={{ ...s.card, position:'relative' }}>
                        <span style={{ position:'absolute', top:'10px', right:'12px', fontSize:'10px', fontWeight:600, padding:'2px 7px', borderRadius:'99px', background: c.source==='website'?'var(--green-bg)':'var(--amber-bg)', color: c.source==='website'?'var(--green-text)':'var(--amber-text)' }}>
                          {c.source==='website' ? '✓ Live site' : 'Generated'}
                        </span>
                        <div style={{ display:'flex', alignItems:'center', gap:'10px', marginBottom:'10px' }}>
                          <div style={{ width:'36px', height:'36px', borderRadius:'50%', display:'flex', alignItems:'center', justifyContent:'center', fontSize:'12px', fontWeight:600, flexShrink:0, background:'var(--accent-bg)', color:'var(--accent-text)' }}>
                            {initials(c.name)}
                          </div>
                          <div>
                            <div style={{ fontSize:'14px', fontWeight:600 }}>{c.name}</div>
                            <div style={{ fontSize:'12px', color:'var(--text-2)' }}>{c.title}</div>
                          </div>
                        </div>
                        <div style={{ fontSize:'12px', borderTop:'1px solid var(--border)', paddingTop:'9px' }}>
                          <div style={{ color:'var(--accent-text)', marginBottom:'4px', wordBreak:'break-all' }}>{c.email}</div>
                          {c.profile_url && <a href={c.profile_url} target="_blank" rel="noreferrer" style={{ fontSize:'11px', color:'var(--text-3)' }}>View source ↗</a>}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
              <div style={{ display:'flex', justifyContent:'flex-end', marginTop:'22px', paddingTop:'18px', borderTop:'1px solid var(--border)' }}>
                <button style={s.btnPrimary} onClick={doCadence}>Build email cadence →</button>
              </div>
            </div>
          )}

          {/* Step 4: Cadence */}
          {!loading && !error && step === 4 && cadences.length > 0 && (
            <div>
              <div style={{ display:'flex', justifyContent:'space-between', alignItems:'flex-start', marginBottom:'18px' }}>
                <div>
                  <h2 style={{ fontSize:'17px', fontWeight:600 }}>Email Cadence</h2>
                  <p style={{ fontSize:'13px', color:'var(--text-2)', marginTop:'3px' }}>{cadences.length} personalized 3-touch sequences ready</p>
                </div>
                <button style={s.btnGhostSm} onClick={() => setStep(3)}>← Back</button>
              </div>

              {cadences.map((cad, ci) => (
                <div key={ci} style={{ border:'1.5px solid var(--border)', borderRadius:'var(--r)', marginBottom:'14px', overflow:'hidden' }}>
                  <div style={{ display:'flex', alignItems:'center', gap:'11px', padding:'13px 15px', background:'var(--bg-2)', borderBottom:'1px solid var(--border)' }}>
                    <div className={AV[ci%4]} style={{ width:'36px', height:'36px', borderRadius:'50%', display:'flex', alignItems:'center', justifyContent:'center', fontSize:'12px', fontWeight:600, flexShrink:0, background:'var(--accent-bg)', color:'var(--accent-text)' }}>
                      {initials(cad.contact_name)}
                    </div>
                    <div style={{ flex:1 }}>
                      <div style={{ fontSize:'14px', fontWeight:600 }}>{esc(cad.contact_name)}</div>
                      <div style={{ fontSize:'12px', color:'var(--text-2)' }}>{esc(cad.company)} · <span style={{ color:'var(--accent-text)' }}>{esc(cad.email)}</span></div>
                    </div>
                    <span style={s.tag}>3 touches · 12 days</span>
                  </div>
                  {(cad.touches||[]).map((t, ti) => {
                    const key = `${ci}-${ti}`
                    const open = openTouches.has(key)
                    return (
                      <div key={ti} style={{ borderTop: ti===0?'none':'1px solid var(--border)' }}>
                        <div onClick={() => toggleTouch(key)} style={{ display:'flex', alignItems:'center', justifyContent:'space-between', padding:'11px 15px', cursor:'pointer' }}>
                          <div style={{ display:'flex', alignItems:'center', gap:'9px', overflow:'hidden' }}>
                            <span style={{ fontSize:'10px', fontWeight:700, padding:'2px 8px', borderRadius:'99px', textTransform:'uppercase', letterSpacing:'0.05em', flexShrink:0, ...TB_STYLES[ti] }}>
                              {TL[ti]}
                            </span>
                            <span style={{ fontSize:'12px', color:'var(--text-3)', flexShrink:0 }}>Day {t.day}</span>
                            <span style={{ fontSize:'12px', color:'var(--text-2)', whiteSpace:'nowrap', overflow:'hidden', textOverflow:'ellipsis' }}>{t.subject}</span>
                          </div>
                          <span style={{ fontSize:'12px', color:'var(--text-3)' }}>{open ? '▴' : '▾'}</span>
                        </div>
                        {open && (
                          <div style={{ padding:'15px', background:'var(--bg)', borderTop:'1px solid var(--border)' }}>
                            <div style={{ fontSize:'12px', color:'var(--text-2)', marginBottom:'11px' }}><strong style={{ color:'var(--text)' }}>Subject:</strong> {t.subject}</div>
                            <div style={{ fontSize:'13px', lineHeight:'1.75', color:'var(--text)', whiteSpace:'pre-wrap' }}>{t.body}</div>
                            <div style={{ display:'flex', justifyContent:'flex-end', marginTop:'12px' }}>
                              <button style={s.btnGhostSm} onClick={(e) => copyTouch(t.subject, t.body, e.currentTarget as HTMLButtonElement)}>Copy email</button>
                            </div>
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              ))}

              {!trackingPushed ? (
                <button onClick={pushToTracking} style={{ display:'inline-flex', alignItems:'center', gap:'6px', padding:'9px 16px', borderRadius:'var(--r-sm)', fontSize:'13px', fontWeight:500, cursor:'pointer', border:'1.5px solid #bbf7d0', background:'var(--green-bg)', color:'var(--green-text)', fontFamily:'inherit', marginTop:'8px' }}>
                  Add all contacts to tracking →
                </button>
              ) : (
                <p style={{ fontSize:'13px', color:'var(--green-text)', marginTop:'10px' }}>
                  ✓ Added to tracking. Switch to the Tracking tab to manage outcomes.
                </p>
              )}
            </div>
          )}
        </div>
      )}

      {/* ── TRACKING TAB ── */}
      {tab === 'tracking' && (
        <div>
          <div style={{ marginBottom:'20px' }}>
            <h2 style={{ fontSize:'17px', fontWeight:600 }}>Outreach Tracker</h2>
            <p style={{ fontSize:'13px', color:'var(--text-2)', marginTop:'3px' }}>Log email status and call outcomes per contact.</p>
          </div>
          <TrackingTable
            tracking={tracking}
            onStatusChange={(id, status) => {
              const updated = tracking.map((t) => t.id === id ? {...t, status} : t)
              saveTracking(updated)
            }}
            onNoteChange={(id, notes) => {
              const updated = tracking.map((t) => t.id === id ? {...t, notes} : t)
              saveTracking(updated)
            }}
            onClear={() => { if (confirm('Clear all tracking data?')) saveTracking([]) }}
          />
        </div>
      )}
    </div>
  )
}
