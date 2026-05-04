"""
Build the self-contained Local_Government_TAM_Dashboard.html.

All data is embedded as inline JSON; no fetch(); works at file://.
Uses Chart.js via CDN. Dark theme. No localStorage/sessionStorage.
"""

import json
import os

from data import TILE_MAP

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.normpath(os.path.join(HERE, "..", "TAM"))
TAM_JSON = os.path.join(OUT_DIR, "tam_data.json")
COMP_JSON = os.path.join(OUT_DIR, "competitors_data.json")
SIGNALS_JSON = os.path.join(OUT_DIR, "signals_data.json")
GREENFIELD_JSON = os.path.join(OUT_DIR, "greenfield_data.json")
NAMES_JSON = os.path.join(HERE, "names_data.json")
GEOJSON_PATH = os.path.join(HERE, "us_states.geojson")
HTML_PATH = os.path.join(OUT_DIR, "Local_Government_TAM_Dashboard.html")


def build():
    with open(TAM_JSON) as f:
        tam = json.load(f)
    with open(COMP_JSON) as f:
        comp = json.load(f)
    with open(NAMES_JSON) as f:
        names = json.load(f)
    with open(SIGNALS_JSON) as f:
        sigs = json.load(f)
    with open(GREENFIELD_JSON) as f:
        gf = json.load(f)
    with open(GEOJSON_PATH) as f:
        geo = json.load(f)

    # Stringify safely for inline embedding
    tam_s = json.dumps(tam, separators=(",", ":"))
    comp_s = json.dumps(comp, separators=(",", ":"))
    names_s = json.dumps(names, separators=(",", ":"))
    sigs_s = json.dumps(sigs, separators=(",", ":"))
    gf_s = json.dumps(gf, separators=(",", ":"))
    geo_s = json.dumps(geo, separators=(",", ":"))
    tile_s = json.dumps(TILE_MAP)

    html = HTML_TEMPLATE.replace("__TAM__", tam_s)\
                        .replace("__COMP__", comp_s)\
                        .replace("__NAMES__", names_s)\
                        .replace("__SIGNALS__", sigs_s)\
                        .replace("__GREENFIELD__", gf_s)\
                        .replace("__GEO__", geo_s)\
                        .replace("__TILEMAP__", tile_s)

    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Wrote {HTML_PATH}  ({len(html)/1024:.1f} KB)")


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Local Government TAM &amp; Competitive Dashboard</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/d3@7/dist/d3.min.js"></script>
<style>
:root{
  --bg:#0f172a; --card:#1e293b; --text:#e2e8f0; --accent:#38bdf8;
  --muted:#94a3b8; --border:#334155; --hot:#ef4444; --warm:#f59e0b;
  --cool:#3b82f6; --green:#10b981;
}
*{box-sizing:border-box}
html,body{margin:0;padding:0;background:var(--bg);color:var(--text);font-family:-apple-system,Segoe UI,Roboto,sans-serif;font-size:13px;line-height:1.45}
a{color:var(--accent);text-decoration:none}
header{padding:18px 28px;border-bottom:1px solid var(--border);display:flex;justify-content:space-between;align-items:center;background:#0b1220}
header h1{margin:0;font-size:18px;letter-spacing:.5px}
header .meta{color:var(--muted);font-size:12px}
nav.tabs{display:flex;gap:0;padding:0 28px;border-bottom:1px solid var(--border);background:#0b1220}
nav.tabs button{background:transparent;color:var(--muted);border:none;padding:14px 22px;cursor:pointer;font-size:13px;font-weight:500;border-bottom:2px solid transparent;transition:.15s}
nav.tabs button:hover{color:var(--text)}
nav.tabs button.active{color:var(--accent);border-bottom-color:var(--accent)}
main{padding:24px 28px;max-width:1500px;margin:0 auto}
.tab{display:none}
.tab.active{display:block}
.grid{display:grid;gap:18px}
.kpis{grid-template-columns:repeat(auto-fit,minmax(180px,1fr))}
.kpi{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:18px}
.kpi .label{color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:.6px}
.kpi .value{font-size:24px;font-weight:600;margin-top:6px}
.kpi .sub{color:var(--muted);font-size:11px;margin-top:4px}
.card{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:16px}
.card h3{margin:0 0 12px 0;font-size:13px;color:var(--text);font-weight:600;text-transform:uppercase;letter-spacing:.5px}
.row2{grid-template-columns:1fr 1fr}
.row3{grid-template-columns:repeat(3,1fr)}
@media (max-width:980px){.row2,.row3{grid-template-columns:1fr}}
.controls{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:16px;align-items:center}
.controls label{color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:.5px;margin-right:4px}
.btn{background:#0b1220;color:var(--text);border:1px solid var(--border);padding:6px 12px;border-radius:6px;cursor:pointer;font-size:12px;transition:.15s}
.btn:hover{border-color:var(--accent)}
.btn.active{background:var(--accent);color:#0b1220;border-color:var(--accent);font-weight:600}
.chip{background:#0b1220;color:var(--muted);border:1px solid var(--border);padding:4px 10px;border-radius:999px;cursor:pointer;font-size:11px;transition:.15s}
.chip:hover{color:var(--text)}
.chip.active{background:var(--accent);color:#0b1220;border-color:var(--accent);font-weight:600}
.tilemap{display:grid;grid-template-columns:repeat(11,minmax(38px,1fr));gap:4px;margin:0 auto;max-width:560px}
.tile{aspect-ratio:1;display:flex;flex-direction:column;align-items:center;justify-content:center;border-radius:4px;font-size:10px;font-weight:600;cursor:pointer;background:#0b1220;border:1px solid var(--border);transition:.1s;color:var(--muted);position:relative;padding:2px}
.tile.empty{background:transparent;border:none;cursor:default;pointer-events:none}
.tile:not(.empty):hover{border-color:var(--accent);transform:scale(1.05)}
.tile.selected{outline:2px solid var(--accent)}
.tile .v{font-size:9px;font-weight:400;color:inherit;margin-top:1px}
.legend{display:flex;align-items:center;gap:6px;font-size:10px;color:var(--muted);margin-top:8px;justify-content:center}
.legend .swatch{width:14px;height:10px;border-radius:2px;display:inline-block;margin:0 2px}
table.heatmap,table.matrix{border-collapse:collapse;width:100%;font-size:11px}
table.heatmap th,table.heatmap td,table.matrix th,table.matrix td{padding:5px 6px;border:1px solid var(--border);text-align:right}
table.heatmap th,table.matrix th{background:#0b1220;color:var(--muted);text-transform:uppercase;letter-spacing:.4px;font-weight:600;font-size:10px}
table.heatmap td:first-child,table.matrix td:first-child{text-align:left;font-weight:600;color:var(--text)}
.scroll{overflow-x:auto;max-height:none}
.search{background:#0b1220;color:var(--text);border:1px solid var(--border);padding:6px 10px;border-radius:6px;width:100%;font-size:12px}
.search:focus{outline:none;border-color:var(--accent)}
.list{max-height:340px;overflow-y:auto;border:1px solid var(--border);border-radius:6px;padding:6px;background:#0b1220}
.list .item{padding:4px 8px;font-size:12px;border-bottom:1px solid var(--border);display:flex;justify-content:space-between;color:var(--muted)}
.list .item:last-child{border-bottom:none}
.list .item .name{color:var(--text)}
.list .item .meta{font-size:10px}
.vendor-cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;margin-bottom:18px}
.vendor-card{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:14px;cursor:pointer;transition:.15s}
.vendor-card:hover{border-color:var(--accent)}
.vendor-card.active{border-color:var(--accent);background:#0b1220}
.vendor-card h4{margin:0;font-size:13px}
.vendor-card .meta{font-size:11px;color:var(--muted);margin-top:4px}
.vendor-card .total{font-size:18px;font-weight:600;color:var(--accent);margin-top:8px}
.threat-high{color:var(--hot)}
.threat-medium{color:var(--warm)}
.threat-low{color:var(--green)}
canvas{max-height:280px}
.note{color:var(--muted);font-size:11px;margin-top:8px}
.spacer{height:18px}
.demo-banner{background:rgba(245,158,11,.1);border:1px solid #f59e0b;color:#fbbf24;padding:10px 14px;border-radius:6px;font-size:12px;margin-bottom:14px}
.demo-banner b{color:#fde68a}
.chip-row{display:inline-flex;gap:6px;flex-wrap:wrap}
.sig-feed{display:flex;flex-direction:column;gap:8px;max-height:560px;overflow-y:auto}
.sig-card{background:#0b1220;border:1px solid var(--border);border-left:3px solid var(--accent);border-radius:6px;padding:10px 12px;display:grid;grid-template-columns:auto 1fr auto;gap:10px;align-items:start}
.sig-card .badge{display:inline-block;padding:2px 8px;border-radius:999px;font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.5px;color:#fff}
.sig-card .meta-line{font-size:11px;color:var(--muted);margin-top:3px}
.sig-card .headline{font-size:13px;font-weight:600;color:var(--text)}
.sig-card .details{font-size:11px;color:var(--muted);margin-top:3px}
.sig-card .right{font-size:10px;color:var(--muted);text-align:right;white-space:nowrap}
.sig-card .right .score{display:block;font-size:14px;color:var(--accent);font-weight:700}
.sig-sev-high{border-left-color:#ef4444}
.sig-sev-medium{border-left-color:#f59e0b}
.sig-sev-low{border-left-color:#64748b}
.actnow{display:flex;flex-direction:column;gap:6px;max-height:340px;overflow-y:auto}
.actnow .act-row{display:grid;grid-template-columns:30px 1fr auto auto;gap:10px;padding:7px 10px;border-radius:5px;background:#0b1220;border:1px solid var(--border);align-items:center;cursor:pointer}
.actnow .act-row:hover{border-color:var(--accent)}
.actnow .act-row.focused{border-color:var(--accent);background:#0f1830}
.actnow .rank{color:var(--muted);font-weight:700;font-size:11px;text-align:center}
.actnow .name{font-size:12px;font-weight:600}
.actnow .sub{font-size:10px;color:var(--muted)}
.actnow .score{font-size:13px;color:var(--accent);font-weight:700}
.actnow .count{font-size:10px;color:var(--muted)}
.small-multiples{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:14px}
.choropleth{width:100%;background:#0b1220;border-radius:6px;border:1px solid var(--border);position:relative;overflow:hidden}
.choropleth svg{width:100%;height:auto;display:block;background:#0b1220}
.choropleth path.state{stroke:#475569;stroke-width:0.6;cursor:pointer;transition:.1s}
.choropleth path.state:hover{stroke:#fff;stroke-width:1.4}
.choropleth path.state.selected{stroke:var(--accent);stroke-width:2}
.choro-tooltip{position:absolute;pointer-events:none;background:#0f172a;border:1px solid var(--accent);color:var(--text);padding:8px 12px;border-radius:6px;font-size:12px;z-index:10;display:none;white-space:nowrap;box-shadow:0 4px 12px rgba(0,0,0,0.5)}
.choro-tooltip b{color:var(--accent)}
select.search{appearance:none;-webkit-appearance:none;background:#0b1220 url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="12" height="8" viewBox="0 0 12 8"><path fill="%2394a3b8" d="M6 8L0 0h12z"/></svg>') no-repeat right 8px center;padding-right:24px}
.list .item .pop{font-size:10px;color:var(--muted)}
.list .item.unknown-pop{opacity:.7}
.list .item.unknown-pop .pop{color:#64748b;font-style:italic}
.gf-row{cursor:pointer}
.gf-row:hover{background:#0f1830}
.gf-row.focused{background:#0f1830;outline:2px solid var(--accent);outline-offset:-2px}
.gf-score{font-weight:700;font-size:14px}
.gf-score-strong{color:#10b981}
.gf-score-mid{color:#f59e0b}
.gf-score-weak{color:#94a3b8}
.gf-status{display:inline-block;padding:2px 8px;border-radius:999px;font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.4px}
.gf-status-greenfield{background:rgba(16,185,129,0.18);color:#34d399}
.gf-status-in-window{background:rgba(239,68,68,0.18);color:#f87171}
.gf-status-imminent{background:rgba(245,158,11,0.18);color:#fbbf24}
.gf-status-warming{background:rgba(56,189,248,0.18);color:#7dd3fc}
.gf-status-past-due{background:rgba(168,85,247,0.18);color:#c4b5fd}
.gf-status-active{background:rgba(100,116,139,0.18);color:#94a3b8}
.gf-status-unknown{background:rgba(100,116,139,0.18);color:#94a3b8}
.gf-detail-section{margin-bottom:14px}
.gf-detail-section h4{margin:0 0 6px 0;font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.5px}
.gf-bar{height:6px;background:#1e293b;border-radius:3px;overflow:hidden;margin-top:3px}
.gf-bar-fill{height:100%;background:var(--accent)}
.gf-component{display:grid;grid-template-columns:auto 1fr auto;gap:8px;font-size:11px;align-items:center;margin-bottom:4px}
.gf-persona{display:flex;justify-content:space-between;font-size:11px;padding:3px 0;border-bottom:1px dotted var(--border)}
.gf-persona:last-child{border-bottom:none}
.gf-persona .role{font-size:9px;color:var(--muted);text-transform:uppercase}
.sm-card{background:#0b1220;border:1px solid var(--border);border-radius:6px;padding:10px}
.sm-card .sm-header{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:6px}
.sm-card .sm-name{font-size:12px;font-weight:600;color:var(--text)}
.sm-card .sm-meta{font-size:10px;color:var(--muted)}
.sm-card .tilemap{max-width:100%;grid-template-columns:repeat(11,minmax(20px,1fr));gap:2px}
.sm-card .tile{font-size:8px;border-radius:2px;padding:0}
.sm-card .tile .v{display:none}
</style>
</head>
<body>

<header>
  <div>
    <h1>Local Government TAM &amp; Competitive Dashboard</h1>
    <div class="meta">U.S. local-gov software market &middot; 2022 Census of Governments &middot; refreshed 2026-05-01</div>
  </div>
  <div class="meta" id="hdrSummary"></div>
</header>

<nav class="tabs">
  <button class="active" data-tab="overview">TAM Overview</button>
  <button data-tab="heatmaps">Heatmaps</button>
  <button data-tab="names">State &amp; Names</button>
  <button data-tab="competitive">Competitive Penetration</button>
  <button data-tab="signals">Buying Signals</button>
  <button data-tab="prospects">Top Prospects</button>
</nav>

<main>

<!-- ===== TAB 1: OVERVIEW ===== -->
<section class="tab active" id="tab-overview">
  <div class="controls">
    <label>Metric:</label>
    <button class="btn active" data-metric="spend">Gov Spend ($)</button>
    <button class="btn" data-metric="acv">Software TAM (ACV)</button>
    <button class="btn" data-metric="count">Entity Count</button>
    <span style="width:18px"></span>
    <label>Type:</label>
    <button class="btn chip-type active" data-type="all">All</button>
    <button class="btn chip-type" data-type="munis">Municipalities</button>
    <button class="btn chip-type" data-type="counties">Counties</button>
    <button class="btn chip-type" data-type="townships">Townships</button>
    <button class="btn chip-type" data-type="special_districts">Special Districts</button>
  </div>

  <div class="grid kpis" id="kpis"></div>
  <div class="spacer"></div>

  <div class="grid row2">
    <div class="card">
      <h3>US Map (logical tile layout)</h3>
      <div id="tileOverview"></div>
      <div class="legend"><span>low</span>
        <span class="swatch" style="background:#1e3a8a;opacity:.2"></span>
        <span class="swatch" style="background:#1e3a8a;opacity:.4"></span>
        <span class="swatch" style="background:#1e3a8a;opacity:.6"></span>
        <span class="swatch" style="background:#1e3a8a;opacity:.85"></span>
        <span class="swatch" style="background:#1e3a8a"></span>
        <span>high</span>
      </div>
    </div>
    <div class="card">
      <h3>Top 15 States</h3>
      <canvas id="topStatesChart"></canvas>
    </div>
  </div>

  <div class="spacer"></div>

  <div class="grid row2">
    <div class="card">
      <h3>By Entity Type</h3>
      <canvas id="entityTypeChart"></canvas>
    </div>
    <div class="card">
      <h3>By Population Bucket</h3>
      <canvas id="bucketChart"></canvas>
    </div>
  </div>
</section>

<!-- ===== TAB 2: HEATMAPS ===== -->
<section class="tab" id="tab-heatmaps">
  <div class="card" style="margin-bottom:18px">
    <h3>US Choropleth Heatmap</h3>
    <div class="controls" style="margin-bottom:12px">
      <label>Metric:</label>
      <button class="btn chip-cmetric active" data-cmetric="spend">Spend</button>
      <button class="btn chip-cmetric" data-cmetric="count">Count</button>
      <button class="btn chip-cmetric" data-cmetric="competitor">Competitor</button>
      <button class="btn chip-cmetric" data-cmetric="penetration">Pen %</button>
      <span style="width:14px"></span>
      <label>Type:</label>
      <select class="search" id="cType" style="max-width:160px">
        <option value="all">All entity types</option>
        <option value="munis">Municipalities</option>
        <option value="counties">Counties</option>
        <option value="townships">Townships</option>
        <option value="special_districts">Special Districts</option>
      </select>
      <label>Size:</label>
      <select class="search" id="cBucket" style="max-width:140px">
        <option value="all">All sizes</option>
      </select>
      <label>Competitor:</label>
      <select class="search" id="cVendor" style="max-width:170px">
        <option value="all">All / none</option>
      </select>
      <input class="search" id="cSearch" placeholder="Search state name&hellip;" style="max-width:180px">
    </div>
    <div id="choropleth" class="choropleth"></div>
    <div class="legend" id="choroLegend"></div>
    <div class="note" id="choroNote"></div>
  </div>

  <div class="grid row2">
    <div class="card">
      <h3>Entity Count Heatmap (state &times; bucket)</h3>
      <div class="controls" style="margin-bottom:8px">
        <label>Type:</label>
        <button class="btn chip-htype active" data-type="all">All (excl. SD)</button>
        <button class="btn chip-htype" data-type="munis">Munis</button>
        <button class="btn chip-htype" data-type="counties">Counties</button>
        <button class="btn chip-htype" data-type="townships">Townships</button>
      </div>
      <div class="scroll"><table class="heatmap" id="heatmapCount"></table></div>
      <div class="note">Cells colored per-column on a log-scaled percentile.</div>
    </div>
    <div class="card">
      <h3>Estimated Annual Spend Heatmap (state &times; bucket)</h3>
      <div style="height:30px"></div>
      <div class="scroll"><table class="heatmap" id="heatmapSpend"></table></div>
      <div class="note">$ in millions; per-column log-scaled percentile.</div>
    </div>
  </div>
</section>

<!-- ===== TAB 3: STATE & NAMES OVERLAY ===== -->
<section class="tab" id="tab-names">
  <div class="grid row2">
    <div class="card">
      <h3>Pick a state</h3>
      <div id="tileNames"></div>
      <div class="note">Click any state tile to load its counties and municipalities.</div>
    </div>
    <div class="card">
      <h3 id="namesHeader">No state selected</h3>
      <div class="controls" style="margin-bottom:8px">
        <input class="search" id="nameSearch" placeholder="Search counties or munis&hellip;">
      </div>
      <div class="controls" id="bucketChips" style="margin-top:0">
        <label>Filter:</label>
      </div>
      <div class="controls" style="margin-top:6px">
        <label>Show:</label>
        <button class="btn chip-mshow active" data-mshow="all">All munis</button>
        <button class="btn chip-mshow" data-mshow="known">Known pop only (&ge;15K)</button>
        <button class="btn chip-mshow" data-mshow="small">Small (&lt;15K)</button>
        <span style="flex:1"></span>
        <button class="btn" id="namesExport">Export to CSV</button>
      </div>
      <div class="grid row2">
        <div>
          <h4 style="font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.5px;margin:8px 0 6px" id="countyHeader">Counties</h4>
          <div class="list" id="countyList"></div>
        </div>
        <div>
          <h4 style="font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.5px;margin:8px 0 6px" id="cityHeader">Municipalities</h4>
          <div class="list" id="cityList"></div>
        </div>
      </div>
      <div class="grid row2" style="margin-top:8px">
        <div>
          <h4 style="font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.5px;margin:8px 0 6px" id="twpHeader">Townships</h4>
          <div class="list" id="twpList"></div>
          <div class="note" id="twpNote" style="margin-top:4px"></div>
        </div>
        <div>
          <h4 style="font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.5px;margin:8px 0 6px" id="sdHeader">Special Districts</h4>
          <div class="list" id="sdList"></div>
          <div class="note" id="sdNote" style="margin-top:4px"></div>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- ===== TAB 4: COMPETITIVE PENETRATION ===== -->
<section class="tab" id="tab-competitive">
  <div class="vendor-cards" id="vendorCards"></div>

  <div class="controls">
    <label>Map shading:</label>
    <button class="btn active" data-vmap="count">Customer count</button>
    <button class="btn" data-vmap="penetration">Penetration % of addressable</button>
  </div>

  <div class="grid row2">
    <div class="card">
      <h3 id="vendorMapTitle">Customer count by state</h3>
      <div id="tileVendor"></div>
      <div class="legend">
        <span>0</span>
        <span class="swatch" style="background:#a855f7;opacity:.15"></span>
        <span class="swatch" style="background:#a855f7;opacity:.35"></span>
        <span class="swatch" style="background:#a855f7;opacity:.55"></span>
        <span class="swatch" style="background:#a855f7;opacity:.8"></span>
        <span class="swatch" style="background:#a855f7"></span>
        <span>peak</span>
      </div>
    </div>
    <div class="card">
      <h3>Top 15 States for selected vendor</h3>
      <canvas id="vendorTopChart"></canvas>
    </div>
  </div>

  <div class="spacer"></div>

  <div class="card">
    <div style="display:flex;justify-content:space-between;align-items:baseline">
      <h3 id="namedCustHeader">Named customers — seed dataset</h3>
      <button class="btn" id="namedCustExport">Export to CSV</button>
    </div>
    <div class="controls" style="margin-bottom:8px">
      <input class="search" id="namedCustSearch" placeholder="Search muni, state, or product&hellip;" style="max-width:280px">
      <span class="note" id="namedCustNote" style="margin:0"></span>
    </div>
    <div class="scroll" style="max-height:380px"><table class="matrix" id="namedCust"></table></div>
  </div>

  <div class="spacer"></div>

  <div class="card">
    <h3>Per-vendor state heatmaps (small multiples)</h3>
    <div class="controls" style="margin-bottom:8px">
      <label>Color by:</label>
      <button class="btn active" data-smallm="count">Customer count</button>
      <button class="btn" data-smallm="penetration">Penetration %</button>
      <span style="flex:1"></span>
      <span class="note" style="margin:0">Each map auto-scales to its own vendor max (a vendor's HQ state is always darkest).</span>
    </div>
    <div id="smallMultiples" class="small-multiples"></div>
  </div>

  <div class="spacer"></div>

  <div class="card">
    <h3>Full vendor &times; state matrix (color = per-vendor percentile)</h3>
    <div class="scroll"><table class="matrix" id="matrix"></table></div>
  </div>
</section>

<!-- ===== TAB 5: BUYING SIGNALS ===== -->
<section class="tab" id="tab-signals">
  <div id="sigDemoBanner" class="demo-banner"></div>

  <div class="grid kpis" id="sigKpis"></div>
  <div class="spacer"></div>

  <div class="controls">
    <label>ICP:</label>
    <button class="btn chip-sicp active" data-sicp="sub15k" title="Default: under 15K population">&lt;15K (ICP)</button>
    <button class="btn chip-sicp" data-sicp="under50k">&lt;50K</button>
    <button class="btn chip-sicp" data-sicp="all">All sizes</button>
    <span style="width:18px"></span>
    <label>Type:</label>
    <span id="sigTypeChips" class="chip-row"></span>
  </div>
  <div class="controls" style="margin-top:6px">
    <label>Severity:</label>
    <button class="btn chip-sev active" data-sev="all">All</button>
    <button class="btn chip-sev" data-sev="high">High</button>
    <button class="btn chip-sev" data-sev="medium">Medium</button>
    <button class="btn chip-sev" data-sev="low">Low</button>
    <span style="flex:1"></span>
    <input class="search" id="sigSearch" placeholder="Search muni or headline&hellip;" style="max-width:260px">
  </div>

  <div class="grid row2">
    <div class="card">
      <h3 id="sigMapTitle">Signal density by state</h3>
      <div id="tileSignals"></div>
      <div class="legend">
        <span>cold</span>
        <span class="swatch" style="background:#ef4444;opacity:.15"></span>
        <span class="swatch" style="background:#ef4444;opacity:.35"></span>
        <span class="swatch" style="background:#ef4444;opacity:.55"></span>
        <span class="swatch" style="background:#ef4444;opacity:.8"></span>
        <span class="swatch" style="background:#ef4444"></span>
        <span>hot</span>
      </div>
      <div class="note">Score = signal weight × recency decay × severity. Click a state to filter the feed.</div>
    </div>
    <div class="card">
      <h3>Act Now leaderboard</h3>
      <div id="actNow" class="actnow"></div>
      <div class="note">Top accounts by composite score. Click a row to focus.</div>
    </div>
  </div>

  <div class="spacer"></div>

  <div class="card">
    <div style="display:flex;justify-content:space-between;align-items:baseline">
      <h3 id="sigFeedTitle">Signal feed</h3>
      <button class="btn" id="sigExport">Export filtered to CSV</button>
    </div>
    <div id="sigFeed" class="sig-feed"></div>
  </div>
</section>

<!-- ===== TAB 6: TOP PROSPECTS ===== -->
<section class="tab" id="tab-prospects">
  <div class="grid kpis" id="gfKpis"></div>
  <div class="spacer"></div>

  <div class="controls">
    <label>State:</label>
    <select class="search" id="gfState" style="max-width:130px">
      <option value="all">All</option>
    </select>
    <label>Bucket:</label>
    <select class="search" id="gfBucket" style="max-width:140px">
      <option value="all">All sizes</option>
    </select>
    <label>Status:</label>
    <button class="btn chip-gfstatus active" data-gfstatus="all">All</button>
    <button class="btn chip-gfstatus" data-gfstatus="greenfield">Greenfield</button>
    <button class="btn chip-gfstatus" data-gfstatus="in-window">In Window</button>
    <button class="btn chip-gfstatus" data-gfstatus="imminent">Imminent</button>
    <button class="btn chip-gfstatus" data-gfstatus="past-due">Past Due</button>
    <button class="btn chip-gfstatus" data-gfstatus="warming">Warming</button>
    <span style="flex:1"></span>
    <input class="search" id="gfSearch" placeholder="Search muni or vendor&hellip;" style="max-width:240px">
    <button class="btn" id="gfExport">Export to CSV</button>
  </div>

  <div class="grid row2">
    <div class="card">
      <h3 id="gfListTitle">Top prospects</h3>
      <div class="scroll" style="max-height:600px"><table class="matrix" id="gfList"></table></div>
    </div>
    <div class="card">
      <h3 id="gfDetailTitle">Click a row for details</h3>
      <div id="gfDetail"></div>
    </div>
  </div>
</section>

</main>

<script>
const TAM = __TAM__;
const COMP = __COMP__;
const NAMES = __NAMES__;
const SIGNALS = __SIGNALS__;
const GREENFIELD = __GREENFIELD__;
const GEO = __GEO__;
const TILEMAP = __TILEMAP__;

// state name -> abbrev
const NAME_TO_ABBR = {};
Object.entries(COMP.state_names).forEach(([abbr, name]) => NAME_TO_ABBR[name] = abbr);

const STATES = Object.keys(TAM.states);
const BUCKETS = TAM.buckets;
const STATE_NAMES = COMP.state_names;

// ----- in-memory UI state (no persistence) -----
const ui = {
  metric: "spend",
  type: "all",
  htype: "all",
  selectedState: null,
  selectedBucket: "all",
  vendor: Object.keys(COMP.vendors)[0],
  vmap: "count",
  smallm: "count",
  sigType: "all",
  sigSev: "all",
  sigIcp: "sub15k",     // default to sub-15K ICP
  sigStateFilter: null,
  sigSearch: "",
  sigFocusKey: null,
  // choropleth filters
  cMetric: "spend",     // spend | count | competitor | penetration
  cType: "all",
  cBucket: "all",
  cVendor: "all",
  cSearch: "",
  cSelectedState: null,
  // names tab extras
  mShow: "all",         // all | known | small
  // named customers
  ncSearch: "",
  // greenfield (Top Prospects)
  gfState: "all",
  gfBucket: "all",
  gfStatus: "all",
  gfSearch: "",
  gfFocusKey: null,
};

// ===== Tabs =====
document.querySelectorAll("nav.tabs button").forEach(b => {
  b.addEventListener("click", () => {
    document.querySelectorAll("nav.tabs button").forEach(x => x.classList.remove("active"));
    b.classList.add("active");
    document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
    document.getElementById("tab-" + b.dataset.tab).classList.add("active");
    // Re-render the choropleth when entering Heatmaps (svg sizes off the
    // container width, which is 0 while hidden)
    if (b.dataset.tab === "heatmaps") setTimeout(renderChoropleth, 10);
  });
});

// ===== Helpers =====
function fmtUsd(n) {
  if (Math.abs(n) >= 1e12) return "$" + (n / 1e12).toFixed(2) + "T";
  if (Math.abs(n) >= 1e9)  return "$" + (n / 1e9).toFixed(1)  + "B";
  if (Math.abs(n) >= 1e6)  return "$" + (n / 1e6).toFixed(1)  + "M";
  if (Math.abs(n) >= 1e3)  return "$" + (n / 1e3).toFixed(0)  + "K";
  return "$" + n.toFixed(0);
}
function fmtInt(n){ return Math.round(n).toLocaleString(); }
function fmtPct(n){ return (n * 100).toFixed(2) + "%"; }

function entityCount(st, type) {
  const c = TAM.states[st].counts;
  if (type === "all") return c.counties + c.munis + c.townships + c.special_districts;
  if (type === "munis") return c.munis;
  if (type === "counties") return c.counties;
  if (type === "townships") return c.townships;
  if (type === "special_districts") return c.special_districts;
}
function spendVal(st, type) {
  const s = TAM.states[st];
  if (type === "all") return s.total_spend;
  if (type === "special_districts") return s.special_districts_spend;
  return s.spend_by_bucket[type].reduce((a,b)=>a+b,0);
}
function acvVal(st, type) {
  const s = TAM.states[st];
  if (type === "all") return s.total_acv;
  if (type === "special_districts") return s.special_districts_acv;
  return (s.acv_by_bucket && s.acv_by_bucket[type]) ? s.acv_by_bucket[type].reduce((a,b)=>a+b,0) : 0;
}
function metricVal(st) {
  if (ui.metric === "spend") return spendVal(st, ui.type);
  if (ui.metric === "acv")   return acvVal(st, ui.type);
  return entityCount(st, ui.type);
}

// ===== Header summary =====
function updateHeaderSummary() {
  const totalSpend = STATES.reduce((s, st) => s + TAM.states[st].total_spend, 0);
  const totalEntities = STATES.reduce((s, st) => s + TAM.states[st].total_entities, 0);
  const totalCustomers = Object.values(COMP.vendors).reduce((s, v) => s + v.allocated, 0);
  document.getElementById("hdrSummary").innerHTML =
    "TAM " + fmtUsd(totalSpend) + " &middot; "
    + fmtInt(totalEntities) + " entities &middot; "
    + fmtInt(totalCustomers) + " tracked customers &middot; "
    + fmtInt(SIGNALS.signals.length) + " active signals";
}

// ===== KPIs =====
function isDollarMetric() { return ui.metric === "spend" || ui.metric === "acv"; }
function metricLabel() {
  return ui.metric === "spend" ? "operating spend"
       : ui.metric === "acv"   ? "software ACV"
       : "entities";
}

function renderKpis() {
  const totalGovSpend = STATES.reduce((s, st) => s + spendVal(st, ui.type), 0);
  const totalAcv      = STATES.reduce((s, st) => s + acvVal(st, ui.type), 0);
  const totalCount    = STATES.reduce((s, st) => s + entityCount(st, ui.type), 0);
  const sorted = STATES.map(st => [st, metricVal(st)]).sort((a,b) => b[1]-a[1]);
  const top1 = sorted[0];
  const top5Share = sorted.slice(0, 5).reduce((s,x) => s + x[1], 0) /
                    sorted.reduce((s,x) => s + x[1], 0);

  const kpis = [
    {label: "Total Gov Spend (TAM)", value: fmtUsd(totalGovSpend), sub: "annual operating, 2022 baseline"},
    {label: "Total Software ACV", value: fmtUsd(totalAcv), sub: "addressable software revenue"},
    {label: "Total entities", value: fmtInt(totalCount), sub: ui.type === "all" ? "all types" : "selected type"},
    {label: "Largest state (" + metricLabel() + ")",
     value: top1[0] + " &middot; " + (isDollarMetric() ? fmtUsd(top1[1]) : fmtInt(top1[1])),
     sub: STATE_NAMES[top1[0]]},
    {label: "Top-5 share", value: fmtPct(top5Share), sub: "of " + metricLabel()},
  ];
  document.getElementById("kpis").innerHTML =
    kpis.map(k => `<div class="kpi"><div class="label">${k.label}</div><div class="value">${k.value}</div><div class="sub">${k.sub}</div></div>`).join("");
}

// ===== Tile map renderer =====
function renderTileMap(containerId, valueFn, opts) {
  opts = opts || {};
  const colorBase = opts.color || "30,58,138";  // RGB; default deep blue
  const c = document.getElementById(containerId);
  c.innerHTML = "";
  c.classList.add("tilemap");

  // Compute max for scaling
  let max = 0;
  STATES.forEach(s => { const v = valueFn(s); if (v > max) max = v; });
  if (max === 0) max = 1;

  // Build grid
  const grid = document.createElement("div");
  grid.className = "tilemap";
  TILEMAP.forEach(row => {
    row.forEach(st => {
      const tile = document.createElement("div");
      tile.className = "tile" + (st === "" ? " empty" : "");
      if (st !== "") {
        const v = valueFn(st);
        const intensity = Math.pow(v / max, 0.5);  // sqrt for visibility
        tile.style.background = `rgba(${colorBase},${0.15 + intensity * 0.85})`;
        tile.innerHTML = `<div>${st}</div><div class="v">${opts.label ? opts.label(v) : ""}</div>`;
        if (opts.onClick) tile.addEventListener("click", () => opts.onClick(st));
        if (opts.selected && st === opts.selected) tile.classList.add("selected");
        // tooltip via title
        tile.title = STATE_NAMES[st] + ": " + (opts.tip ? opts.tip(v) : v);
      }
      grid.appendChild(tile);
    });
  });
  c.appendChild(grid);
}

// ===== Charts (recreated on each render) =====
let charts = {};
function destroyChart(key) {
  if (charts[key]) { charts[key].destroy(); charts[key] = null; }
}

function renderTopStates() {
  destroyChart("topStates");
  const sorted = STATES.map(st => [st, metricVal(st)]).sort((a,b) => b[1]-a[1]).slice(0, 15);
  const ctx = document.getElementById("topStatesChart").getContext("2d");
  const fmt = isDollarMetric() ? fmtUsd : fmtInt;
  charts.topStates = new Chart(ctx, {
    type: "bar",
    data: { labels: sorted.map(x => x[0]),
            datasets: [{ data: sorted.map(x => x[1]),
                         backgroundColor: "#38bdf8" }] },
    options: { indexAxis: "y", responsive: true, maintainAspectRatio: false,
               plugins: { legend: { display: false },
                          tooltip: { callbacks: { label: (c) => fmt(c.parsed.x) } } },
               scales: { x: { ticks: { color: "#94a3b8", callback: v => fmt(v) }, grid: { color: "#334155" } },
                         y: { ticks: { color: "#e2e8f0" }, grid: { display: false } } } }
  });
}

function renderEntityTypeChart() {
  destroyChart("entityType");
  const types = ["counties", "munis", "townships", "special_districts"];
  const labels = ["Counties", "Munis", "Townships", "Special Districts"];
  const fn = ui.metric === "spend" ? spendVal : ui.metric === "acv" ? acvVal : (st, t) => entityCount(st, t);
  const fmt = isDollarMetric() ? fmtUsd : fmtInt;
  const values = types.map(t => STATES.reduce((s, st) => s + fn(st, t), 0));
  const ctx = document.getElementById("entityTypeChart").getContext("2d");
  charts.entityType = new Chart(ctx, {
    type: "doughnut",
    data: { labels, datasets: [{ data: values, backgroundColor: ["#38bdf8", "#a855f7", "#10b981", "#f59e0b"], borderColor: "#1e293b", borderWidth: 2 }] },
    options: { responsive: true, maintainAspectRatio: false,
               plugins: { legend: { position: "bottom", labels: { color: "#e2e8f0", font: { size: 11 } } },
                          tooltip: { callbacks: { label: (c) => c.label + ": " + fmt(c.parsed) } } } }
  });
}

function renderBucketChart() {
  destroyChart("bucket");
  const types = ui.type === "all" ? ["munis", "counties", "townships"] :
                (ui.type === "special_districts" ? [] : [ui.type]);
  const values = BUCKETS.map((_, i) => {
    let total = 0;
    STATES.forEach(st => {
      types.forEach(t => {
        if (ui.metric === "spend") total += TAM.states[st].spend_by_bucket[t][i];
        else if (ui.metric === "acv") total += (TAM.states[st].acv_by_bucket && TAM.states[st].acv_by_bucket[t] ? TAM.states[st].acv_by_bucket[t][i] : 0);
        else total += TAM.states[st].by_bucket[t][i];
      });
    });
    return total;
  });
  const ctx = document.getElementById("bucketChart").getContext("2d");
  const fmt = isDollarMetric() ? fmtUsd : fmtInt;
  charts.bucket = new Chart(ctx, {
    type: "bar",
    data: { labels: BUCKETS, datasets: [{ data: values, backgroundColor: "#a855f7" }] },
    options: { responsive: true, maintainAspectRatio: false,
               plugins: { legend: { display: false },
                          tooltip: { callbacks: { label: (c) => fmt(c.parsed.y) } } },
               scales: { x: { ticks: { color: "#e2e8f0" }, grid: { display: false } },
                         y: { ticks: { color: "#94a3b8", callback: v => fmt(v) }, grid: { color: "#334155" } } } }
  });
}

function renderOverview() {
  renderKpis();
  const fmt = isDollarMetric() ? fmtUsd : fmtInt;
  renderTileMap("tileOverview", metricVal, {
    color: "30,58,138",
    label: v => fmt(v),
    tip: v => fmt(v),
  });
  renderTopStates();
  renderEntityTypeChart();
  renderBucketChart();
}

// ===== Heatmaps =====
function logPercentileColor(v, sortedNonZero, hue) {
  if (v <= 0) return "rgba(15,23,42,0.5)";
  const log = Math.log(v + 1);
  const logs = sortedNonZero.map(x => Math.log(x + 1));
  const min = logs[0], max = logs[logs.length - 1];
  const range = max - min || 1;
  const t = (log - min) / range;
  return `hsla(${hue}, 80%, ${20 + (1 - t) * 50}%, 1)`;
}

function buildHeatmap(tableId, getter, hue) {
  const table = document.getElementById(tableId);
  const types = ui.htype === "all" ? ["munis", "counties", "townships"] : [ui.htype];

  // Compute per-bucket column for sorting/coloring
  const matrix = STATES.map(st => {
    const row = BUCKETS.map((_, i) => types.reduce((s, t) => s + getter(st, t, i), 0));
    return [st, row];
  });

  // Per-column percentile coloring
  const cols = BUCKETS.map((_, i) => {
    const vals = matrix.map(m => m[1][i]).filter(v => v > 0).sort((a,b) => a-b);
    return vals;
  });

  let html = "<thead><tr><th>State</th>" + BUCKETS.map(b => `<th>${b}</th>`).join("") + "<th>Row Total</th></tr></thead><tbody>";
  matrix.sort((a,b) => b[1].reduce((s,x)=>s+x,0) - a[1].reduce((s,x)=>s+x,0));
  matrix.forEach(([st, row]) => {
    const total = row.reduce((s,x)=>s+x,0);
    html += "<tr><td>" + st + "</td>" +
      row.map((v, i) => `<td style="background:${logPercentileColor(v, cols[i], hue)};color:#fff">${formatHeatVal(v, hue)}</td>`).join("") +
      `<td style="font-weight:600">${formatHeatVal(total, hue)}</td></tr>`;
  });
  html += "</tbody>";
  table.innerHTML = html;
}
function formatHeatVal(v, hue) {
  if (hue === 220) return fmtInt(v);  // count (blue)
  return fmtUsd(v);                    // spend (orange)
}
function renderHeatmaps() {
  buildHeatmap("heatmapCount",
    (st, t, i) => TAM.states[st].by_bucket[t][i], 220);
  buildHeatmap("heatmapSpend",
    (st, t, i) => TAM.states[st].spend_by_bucket[t][i], 30);
}

// ===== State & Names overlay =====
function renderNamesTile() {
  renderTileMap("tileNames",
    st => TAM.states[st].total_entities,
    {
      color: "16,185,129",
      label: st => "",
      onClick: selectState,
      selected: ui.selectedState,
      tip: v => fmtInt(v) + " entities"
    });
}
function selectState(st) {
  ui.selectedState = st;
  renderNamesTile();
  renderNamesPanel();
}
function renderBucketChips() {
  const c = document.getElementById("bucketChips");
  c.innerHTML = '<label>Bucket:</label>';
  ["all", ...BUCKETS, "small (<15K)"].forEach(b => {
    const btn = document.createElement("button");
    btn.className = "chip" + (ui.selectedBucket === b ? " active" : "");
    btn.textContent = b === "all" ? "All" : b;
    btn.addEventListener("click", () => { ui.selectedBucket = b; renderBucketChips(); renderLists(); });
    c.appendChild(btn);
  });
}
function renderNamesPanel() {
  const hdr = document.getElementById("namesHeader");
  if (!ui.selectedState) {
    hdr.textContent = "No state selected";
    return;
  }
  const st = ui.selectedState;
  const data = NAMES[st] || { counties: [], cities: [] };
  const entities = TAM.states[st].counts;
  hdr.innerHTML = STATE_NAMES[st] + " (" + st + ") &middot; " +
    fmtInt(entities.counties) + " counties &middot; " +
    fmtInt(entities.munis) + " munis &middot; " +
    fmtInt(entities.townships) + " townships &middot; " +
    fmtInt(entities.special_districts) + " SDs &middot; TAM " + fmtUsd(TAM.states[st].total_spend);
  renderBucketChips();
  renderLists();
}
function namesFilteredCities() {
  if (!ui.selectedState) return [];
  const st = ui.selectedState;
  const data = NAMES[st] || { counties: [], cities: [] };
  const q = (document.getElementById("nameSearch").value || "").toLowerCase();
  let cities = data.cities;
  if (ui.mShow === "known") cities = cities.filter(c => c.pop !== null);
  else if (ui.mShow === "small") cities = cities.filter(c => c.pop === null);
  if (ui.selectedBucket !== "all") cities = cities.filter(c => c.bucket === ui.selectedBucket);
  if (q) cities = cities.filter(c => c.name.toLowerCase().includes(q));
  return cities;
}

function renderLists() {
  if (!ui.selectedState) return;
  const st = ui.selectedState;
  const data = NAMES[st] || { counties: [], cities: [] };
  const q = (document.getElementById("nameSearch").value || "").toLowerCase();

  // Counties
  const filteredCounties = data.counties.filter(c => !q || c.name.toLowerCase().includes(q));
  const cl = document.getElementById("countyList");
  cl.innerHTML = filteredCounties
    .map(c => `<div class="item"><span class="name">${c.name}</span><span class="meta">${c.fips || ""}</span></div>`)
    .join("") || '<div class="item"><span class="name">No counties</span></div>';
  document.getElementById("countyHeader").textContent = `Counties (${filteredCounties.length})`;

  // Munis
  const cities = namesFilteredCities();
  const cityList = document.getElementById("cityList");
  cityList.innerHTML = cities
    .map(c => {
      const popStr = c.pop !== null ? fmtInt(c.pop) : "<15K (unknown)";
      const cls = c.pop === null ? " unknown-pop" : "";
      const buyer = (GREENFIELD.personas_by_bucket[c.bucket] || [])[0] || "";
      const buyerStr = buyer ? ` &middot; <span style="color:var(--accent);font-size:10px">${buyer}</span>` : "";
      return `<div class="item${cls}"><span class="name">${c.name}</span>`
        + `<span class="meta"><span class="pop">${popStr}</span> &middot; ${c.bucket}${buyerStr}</span></div>`;
    })
    .join("") || '<div class="item"><span class="name">No munis match filter</span></div>';
  // Pull total counts for the header
  const totalKnown = data.cities.filter(c => c.pop !== null).length;
  const totalSmall = data.cities.length - totalKnown;
  document.getElementById("cityHeader").textContent =
    `Municipalities (${cities.length}/${data.cities.length}) · ${totalKnown} known + ${totalSmall} small`;

  // Townships
  const twps = (data.townships || []).filter(t => !q || t.name.toLowerCase().includes(q));
  const twpList = document.getElementById("twpList");
  const twpTotal = data._township_count !== undefined ? data._township_count : (data.townships || []).length;
  const twpReal = (data.townships || []).filter(t => t.real).length;
  if (twpTotal === 0) {
    twpList.innerHTML = '<div class="item"><span class="name">No townships in this state</span></div>';
    document.getElementById("twpNote").textContent = "";
  } else if (twpReal === 0) {
    twpList.innerHTML = twps.slice(0, 50).map(t =>
      `<div class="item unknown-pop"><span class="name">${t.name}</span><span class="meta">placeholder</span></div>`).join("");
    document.getElementById("twpNote").innerHTML =
      `<span style="color:#fbbf24">Names not loaded.</span> Showing ${twps.length} placeholders of ${fmtInt(twpTotal)} total. ` +
      `Drop Census Gazetteer <code>2023_Gaz_cousubs_national.txt</code> in <code>build/data_extras/</code> and re-run <code>build_names_data.py</code> for real names.`;
  } else {
    twpList.innerHTML = twps.slice(0, 200).map(t =>
      `<div class="item"><span class="name">${t.name}</span><span class="meta">${t.geoid || ''}</span></div>`).join("");
    document.getElementById("twpNote").textContent = `${twps.length} of ${twpTotal} townships`;
  }
  document.getElementById("twpHeader").textContent =
    `Townships (${twpTotal === 0 ? '0' : (twps.length + ' / ' + fmtInt(twpTotal))})`;

  // Special Districts
  const sds = (data.special_districts || []).filter(s => !q || s.name.toLowerCase().includes(q));
  const sdList = document.getElementById("sdList");
  const sdTotal = data._sd_count !== undefined ? data._sd_count : (data.special_districts || []).length;
  const sdReal = (data.special_districts || []).filter(s => s.real).length;
  if (sdTotal === 0) {
    sdList.innerHTML = '<div class="item"><span class="name">No special districts in this state</span></div>';
    document.getElementById("sdNote").textContent = "";
  } else if (sdReal === 0) {
    sdList.innerHTML = sds.slice(0, 50).map(s =>
      `<div class="item unknown-pop"><span class="name">${s.name}</span><span class="meta">placeholder</span></div>`).join("");
    document.getElementById("sdNote").innerHTML =
      `<span style="color:#fbbf24">Names not loaded.</span> Showing ${sds.length} placeholders of ${fmtInt(sdTotal)} total. ` +
      `Drop a CSV (<code>state,name,type</code>) in <code>build/data_extras/special_districts.csv</code> and re-run.`;
  } else {
    sdList.innerHTML = sds.slice(0, 200).map(s =>
      `<div class="item"><span class="name">${s.name}</span><span class="meta">${s.type || ''}</span></div>`).join("");
    document.getElementById("sdNote").textContent = `${sds.length} of ${sdTotal} special districts`;
  }
  document.getElementById("sdHeader").textContent =
    `Special Districts (${sdTotal === 0 ? '0' : (sds.length + ' / ' + fmtInt(sdTotal))})`;
}

function exportNamesCsv() {
  if (!ui.selectedState) return;
  const st = ui.selectedState;
  const data = NAMES[st] || {};
  const cities = namesFilteredCities();
  const header = "type,name,state,population,bucket,latitude,longitude,extra";
  const rows = [];
  // counties
  (data.counties || []).forEach(c => rows.push([
    "county", c.name, st, "", "", "", "", c.fips || ""
  ]));
  // munis
  cities.forEach(c => rows.push([
    "muni",
    JSON.stringify(c.name).slice(1, -1),
    st,
    c.pop !== null ? c.pop : "",
    c.bucket,
    c.lat !== null ? c.lat : "",
    c.lon !== null ? c.lon : "",
    "",
  ]));
  // townships
  (data.townships || []).forEach(t => rows.push([
    "township", t.name, st, "", "", "", "", t.geoid || ""
  ]));
  // special districts
  (data.special_districts || []).forEach(s => rows.push([
    "special_district", s.name, st, "", "", "", "", s.type || ""
  ]));
  const csv = [header, ...rows.map(r => r.map(v =>
    /[",\n]/.test(String(v)) ? '"' + String(v).replace(/"/g, '""') + '"' : v
  ).join(","))].join("\n");
  const blob = new Blob([csv], {type: "text/csv"});
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = `munis_${st}.csv`;
  document.body.appendChild(a); a.click(); document.body.removeChild(a);
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

// ===== Competitive =====
function renderVendorCards() {
  const c = document.getElementById("vendorCards");
  c.innerHTML = Object.entries(COMP.vendors).map(([name, v]) =>
    `<div class="vendor-card${name === ui.vendor ? ' active' : ''}" data-vendor="${name}">
      <h4>${name}</h4>
      <div class="meta">${v.hq_state_full} &middot; ${v.size_target}</div>
      <div class="total">${fmtInt(v.allocated)} <span style="font-size:11px;color:var(--muted)">customers</span></div>
      <div class="meta">Threat: <span class="threat-${v.threat}">${v.threat}</span></div>
    </div>`).join("");
  c.querySelectorAll(".vendor-card").forEach(el => {
    el.addEventListener("click", () => {
      ui.vendor = el.dataset.vendor;
      renderVendorCards();
      renderVendorMap();
      renderVendorTopChart();
      renderNamedCustomers();
    });
  });
}

function renderVendorMap() {
  const v = COMP.vendors[ui.vendor];
  const fn = (st) => {
    if (ui.vmap === "count") return v.by_state[st] || 0;
    const addr = COMP.addressable_by_state[st] || 1;
    return (v.by_state[st] || 0) / addr;
  };
  document.getElementById("vendorMapTitle").textContent =
    (ui.vmap === "count" ? "Customer count" : "Penetration % of addressable") + " — " + ui.vendor;
  renderTileMap("tileVendor", fn, {
    color: "168,85,247",
    label: v_ => ui.vmap === "count" ? (v_ ? fmtInt(v_) : "") : (v_ > 0 ? (v_ * 100).toFixed(1) + "%" : ""),
    tip: v_ => ui.vmap === "count" ? fmtInt(v_) + " customers" : (v_ * 100).toFixed(2) + "% of addressable",
  });
}
function renderVendorTopChart() {
  destroyChart("vendorTop");
  const v = COMP.vendors[ui.vendor];
  const sorted = STATES.map(st => [st, v.by_state[st] || 0]).sort((a,b) => b[1] - a[1]).slice(0, 15);
  const ctx = document.getElementById("vendorTopChart").getContext("2d");
  charts.vendorTop = new Chart(ctx, {
    type: "bar",
    data: { labels: sorted.map(x => x[0]), datasets: [{ data: sorted.map(x => x[1]), backgroundColor: "#a855f7" }] },
    options: { indexAxis: "y", responsive: true, maintainAspectRatio: false,
               plugins: { legend: { display: false },
                          tooltip: { callbacks: { label: (c) => fmtInt(c.parsed.x) + " customers" } } },
               scales: { x: { ticks: { color: "#94a3b8" }, grid: { color: "#334155" } },
                         y: { ticks: { color: "#e2e8f0" }, grid: { display: false } } } }
  });
}
function vendorCellColor(v, max) {
  if (v <= 0 || max <= 0) return "rgba(15,23,42,0.4)";
  const t = Math.pow(v / max, 0.55);
  // purple ramp matching the per-vendor map
  return `rgba(168,85,247,${0.15 + t * 0.85})`;
}

function renderMatrix() {
  const t = document.getElementById("matrix");
  const vendors = Object.keys(COMP.vendors);

  // Per-vendor max for column-wise coloring
  const vmax = {};
  vendors.forEach(v => {
    vmax[v] = Math.max.apply(null, STATES.map(st => COMP.vendors[v].by_state[st] || 0));
  });
  const combinedMax = Math.max.apply(null, STATES.map(st =>
    vendors.reduce((s, v) => s + (COMP.vendors[v].by_state[st] || 0), 0)));
  const penArr = STATES.map(st => {
    const addr = COMP.addressable_by_state[st] || 1;
    const c = vendors.reduce((s, v) => s + (COMP.vendors[v].by_state[st] || 0), 0);
    return c / addr;
  });
  const penMax = Math.max.apply(null, penArr);

  let html = "<thead><tr><th>State</th>" +
    vendors.map(v => `<th>${v}</th>`).join("") +
    "<th>Combined</th><th>Pen %</th></tr></thead><tbody>";
  STATES.forEach(st => {
    const addr = COMP.addressable_by_state[st] || 1;
    const combined = vendors.reduce((s, v) => s + (COMP.vendors[v].by_state[st] || 0), 0);
    const pen = combined / addr;
    html += "<tr><td>" + st + "</td>" +
      vendors.map(v => {
        const x = COMP.vendors[v].by_state[st] || 0;
        const bg = vendorCellColor(x, vmax[v]);
        const fg = x > vmax[v] * 0.5 ? "#fff" : "var(--text)";
        return `<td style="background:${bg};color:${fg}">${fmtInt(x)}</td>`;
      }).join("") +
      `<td style="background:${vendorCellColor(combined, combinedMax)};color:${combined > combinedMax * 0.5 ? '#fff' : 'var(--text)'};font-weight:600">${fmtInt(combined)}</td>` +
      `<td style="background:rgba(16,185,129,${0.15 + Math.pow(pen / (penMax || 1), 0.55) * 0.85});color:${pen > penMax * 0.5 ? '#fff' : 'var(--text)'};font-weight:600">${(pen * 100).toFixed(2)}%</td></tr>`;
  });
  html += "</tbody>";
  t.innerHTML = html;
}

function renderSmallMultiples() {
  const container = document.getElementById("smallMultiples");
  const mode = ui.smallm;  // "count" | "penetration"
  const vendors = Object.entries(COMP.vendors);

  let html = "";
  vendors.forEach(([name, v]) => {
    // Per-vendor values + max
    const vals = {};
    let max = 0;
    STATES.forEach(st => {
      const cnt = v.by_state[st] || 0;
      const x = mode === "count"
        ? cnt
        : (cnt / (COMP.addressable_by_state[st] || 1));
      vals[st] = x;
      if (x > max) max = x;
    });
    if (max === 0) max = 1;

    // Top state
    const sorted = STATES.map(st => [st, v.by_state[st] || 0]).sort((a,b) => b[1] - a[1]);
    const topSt = sorted[0];

    // Tilemap HTML
    let tmHtml = '<div class="tilemap">';
    TILEMAP.forEach(row => {
      row.forEach(st => {
        if (st === "") {
          tmHtml += '<div class="tile empty"></div>';
        } else {
          const x = vals[st] || 0;
          const intensity = Math.pow(x / max, 0.55);
          const bg = `rgba(168,85,247,${0.15 + intensity * 0.85})`;
          const tip = mode === "count"
            ? `${STATE_NAMES[st]}: ${fmtInt(x)} customers`
            : `${STATE_NAMES[st]}: ${(x * 100).toFixed(2)}% of addressable`;
          tmHtml += `<div class="tile" style="background:${bg};color:#fff" title="${tip}">${st}</div>`;
        }
      });
    });
    tmHtml += '</div>';

    const subTitle = mode === "count"
      ? `${fmtInt(v.allocated)} customers · top state ${topSt[0]} (${fmtInt(topSt[1])})`
      : `peak ${(max * 100).toFixed(1)}% in ${
          STATES.map(st => [st, vals[st]]).sort((a,b)=>b[1]-a[1])[0][0]
        }`;

    html += `<div class="sm-card">
      <div class="sm-header">
        <span class="sm-name">${name}</span>
        <span class="sm-meta threat-${v.threat}">${v.threat.toUpperCase()}</span>
      </div>
      ${tmHtml}
      <div class="sm-meta" style="margin-top:6px">${subTitle}</div>
    </div>`;
  });
  container.innerHTML = html;
}

// ===== Choropleth (Heatmaps tab) =====
function choroplethValue(st) {
  // Returns the metric value for one state given current cMetric/cType/cBucket/cVendor
  const types = ui.cType === "all"
    ? ["munis", "counties", "townships"]
    : (ui.cType === "special_districts" ? [] : [ui.cType]);
  const buckets = ui.cBucket === "all"
    ? BUCKETS.map((_, i) => i)
    : [BUCKETS.indexOf(ui.cBucket)].filter(i => i >= 0);

  if (ui.cMetric === "competitor") {
    if (ui.cVendor === "all") {
      return Object.values(COMP.vendors).reduce((s, v) => s + (v.by_state[st] || 0), 0);
    }
    return COMP.vendors[ui.cVendor]?.by_state[st] || 0;
  }
  if (ui.cMetric === "penetration") {
    const addr = COMP.addressable_by_state[st] || 1;
    const cust = ui.cVendor === "all"
      ? Object.values(COMP.vendors).reduce((s, v) => s + (v.by_state[st] || 0), 0)
      : (COMP.vendors[ui.cVendor]?.by_state[st] || 0);
    return cust / addr;
  }
  // Spend or Count over filtered type+bucket
  let sum = 0;
  if (ui.cType === "special_districts" || (ui.cType === "all" && ui.cBucket === "all")) {
    if (ui.cMetric === "spend") {
      sum += TAM.states[st].special_districts_spend;
    } else {
      sum += TAM.states[st].counts.special_districts;
    }
  }
  types.forEach(t => {
    buckets.forEach(i => {
      if (ui.cMetric === "spend") sum += TAM.states[st].spend_by_bucket[t][i];
      else sum += TAM.states[st].by_bucket[t][i];
    });
  });
  return sum;
}

function choroplethLabelForMetric() {
  if (ui.cMetric === "competitor") {
    return ui.cVendor === "all" ? "Combined customers" : `${ui.cVendor} customers`;
  }
  if (ui.cMetric === "penetration") {
    return ui.cVendor === "all" ? "Combined penetration % of addressable" : `${ui.cVendor} pen %`;
  }
  const t = ui.cType === "all" ? "All entities" : ui.cType.replace("_", " ");
  const b = ui.cBucket === "all" ? "" : ` · ${ui.cBucket}`;
  return `${ui.cMetric === "spend" ? "Spend" : "Count"} · ${t}${b}`;
}

function fmtChoroVal(v) {
  if (ui.cMetric === "spend") return fmtUsd(v);
  if (ui.cMetric === "penetration") return (v * 100).toFixed(2) + "%";
  return fmtInt(v);
}

function fillChoroSelectors() {
  const t = document.getElementById("cType");
  if (t.dataset.filled !== "1") {
    t.dataset.filled = "1";
    t.value = ui.cType;
    t.addEventListener("change", () => { ui.cType = t.value; renderChoropleth(); });
  }
  const b = document.getElementById("cBucket");
  if (b.dataset.filled !== "1") {
    BUCKETS.forEach(bk => {
      const o = document.createElement("option");
      o.value = bk; o.textContent = bk;
      b.appendChild(o);
    });
    b.dataset.filled = "1";
    b.addEventListener("change", () => { ui.cBucket = b.value; renderChoropleth(); });
  }
  const vSel = document.getElementById("cVendor");
  if (vSel.dataset.filled !== "1") {
    Object.keys(COMP.vendors).forEach(v => {
      const o = document.createElement("option");
      o.value = v; o.textContent = v;
      vSel.appendChild(o);
    });
    vSel.dataset.filled = "1";
    vSel.addEventListener("change", () => { ui.cVendor = vSel.value; renderChoropleth(); });
  }
  const s = document.getElementById("cSearch");
  if (s.dataset.filled !== "1") {
    s.dataset.filled = "1";
    s.addEventListener("input", () => { ui.cSearch = s.value.toLowerCase(); renderChoropleth(); });
  }
}

function renderChoropleth() {
  fillChoroSelectors();
  const container = document.getElementById("choropleth");
  container.innerHTML = "";

  // Compute per-state values; respect search filter (greys out non-matches)
  const vals = {};
  STATES.forEach(st => vals[st] = choroplethValue(st));
  const max = Math.max.apply(null, Object.values(vals));
  const min = 0;

  // Pick color ramp by metric
  const ramp = ui.cMetric === "spend" ? [255, 100, 0]
            : ui.cMetric === "competitor" ? [168, 85, 247]
            : ui.cMetric === "penetration" ? [16, 185, 129]
            : [56, 189, 248];

  // Build SVG via d3.geoAlbersUsa
  const w = Math.min(container.clientWidth || 900, 1100);
  const h = Math.round(w * 0.6);
  const svg = d3.create("svg")
    .attr("viewBox", `0 0 ${w} ${h}`)
    .attr("xmlns", "http://www.w3.org/2000/svg");
  const projection = d3.geoAlbersUsa().scale(w * 1.2).translate([w / 2, h / 2]);
  const path = d3.geoPath(projection);

  // Tooltip
  const tip = document.createElement("div");
  tip.className = "choro-tooltip";
  container.appendChild(tip);

  GEO.features.forEach(f => {
    const stateName = f.properties.name;
    const abbr = NAME_TO_ABBR[stateName];
    if (!abbr) return;
    const v = vals[abbr] || 0;
    let intensity = max > 0 ? Math.pow(v / max, 0.55) : 0;
    let bg = `rgba(${ramp[0]},${ramp[1]},${ramp[2]},${0.1 + intensity * 0.85})`;

    // Search filter — non-matches go grey
    if (ui.cSearch && !stateName.toLowerCase().includes(ui.cSearch) && !abbr.toLowerCase().includes(ui.cSearch)) {
      bg = "rgba(100,116,139,0.1)";
    }

    const p = svg.append("path")
      .attr("class", "state" + (ui.cSelectedState === abbr ? " selected" : ""))
      .attr("d", path(f))
      .attr("fill", bg)
      .attr("data-state", abbr);

    p.on("mousemove", function(ev) {
      tip.style.display = "block";
      const r = container.getBoundingClientRect();
      tip.style.left = (ev.clientX - r.left + 12) + "px";
      tip.style.top = (ev.clientY - r.top + 12) + "px";
      tip.innerHTML = `<b>${stateName}</b> (${abbr})<br>${choroplethLabelForMetric()}: ${fmtChoroVal(v)}`;
    });
    p.on("mouseleave", () => { tip.style.display = "none"; });
    p.on("click", () => {
      ui.cSelectedState = (ui.cSelectedState === abbr) ? null : abbr;
      renderChoropleth();
    });

    // State abbrev label centered on the projection
    const c = path.centroid(f);
    if (!isNaN(c[0])) {
      svg.append("text")
        .attr("x", c[0]).attr("y", c[1])
        .attr("text-anchor", "middle").attr("dy", "0.35em")
        .attr("fill", intensity > 0.6 ? "#fff" : "#cbd5e1")
        .attr("font-size", "10")
        .attr("font-weight", "600")
        .attr("pointer-events", "none")
        .text(abbr);
    }
  });

  container.appendChild(svg.node());

  // Legend + note
  document.getElementById("choroLegend").innerHTML =
    `<span>0</span>` +
    [0.15, 0.35, 0.55, 0.8, 1.0].map(i =>
      `<span class="swatch" style="background:rgba(${ramp[0]},${ramp[1]},${ramp[2]},${i})"></span>`).join("") +
    `<span>${fmtChoroVal(max)}</span>`;
  document.getElementById("choroNote").textContent =
    `Showing: ${choroplethLabelForMetric()}.` +
    (ui.cSelectedState ? ` Selected: ${ui.cSelectedState}.` : " Click a state to select; click again to clear.");
}

// ===== Named customers (Competitive tab) =====
function renderNamedCustomers() {
  const v = COMP.vendors[ui.vendor];
  const list = (v.named_customers || []).slice();
  const q = ui.ncSearch.toLowerCase();
  const filt = list.filter(c =>
    !q || c.muni.toLowerCase().includes(q)
       || c.state.toLowerCase().includes(q)
       || (c.product || "").toLowerCase().includes(q)
  );
  document.getElementById("namedCustHeader").textContent =
    `Named customers — ${ui.vendor} (${filt.length}/${list.length} shown)`;
  document.getElementById("namedCustNote").innerHTML =
    `<span style="color:#fbbf24">Demo dataset.</span> Replace with real case-study scrapes (see competitor_customers.py).`;
  const t = document.getElementById("namedCust");
  if (filt.length === 0) {
    t.innerHTML = "<thead><tr><th>—</th></tr></thead><tbody><tr><td>No customers seeded for this vendor or filter.</td></tr></tbody>";
    return;
  }
  let html = "<thead><tr><th>Customer</th><th>State</th><th>Bucket</th><th>Product</th><th>Since</th><th>Renewal</th><th>Est. ACV</th><th>Primary Buyer</th><th>Source</th></tr></thead><tbody>";
  filt.forEach(c => {
    const status = c.renewal_status || "unknown";
    const statusBadge = `<span class="${gfStatusClass(status)}" title="${c.renewal_label || ''}">${status}</span>`;
    const acvStr = c.acv_mid
      ? `${fmtUsd(c.acv_mid)}<div style="font-size:9px;color:var(--muted)">${fmtUsd(c.acv_low)}–${fmtUsd(c.acv_high)}</div>`
      : "—";
    html += `<tr>
      <td>${c.muni}</td>
      <td>${c.state}</td>
      <td>${c.bucket || "—"}</td>
      <td>${c.product || "—"}</td>
      <td>${c.since || "—"}</td>
      <td>${statusBadge}</td>
      <td>${acvStr}</td>
      <td>${c.primary_buyer || "—"}</td>
      <td><span class="meta" style="color:var(--muted);font-size:10px">${c.source || ""}</span></td>
    </tr>`;
  });
  html += "</tbody>";
  t.innerHTML = html;
}

function exportNamedCustomersCsv() {
  const v = COMP.vendors[ui.vendor];
  const list = (v.named_customers || []);
  if (!list.length) return;
  const cols = ["vendor", "muni", "state", "type", "bucket", "product", "since", "source", "demo"];
  const escape = x => {
    if (x === null || x === undefined) return "";
    const s = String(x).replace(/"/g, '""');
    return /[",\n]/.test(s) ? '"' + s + '"' : s;
  };
  const csv = [cols.join(",")]
    .concat(list.map(c => cols.map(k => escape(c[k] !== undefined ? c[k] : ui.vendor)).join(",")))
    .join("\n");
  const blob = new Blob([csv], {type: "text/csv"});
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = `customers_${ui.vendor.replace(/[^a-z0-9]/gi, '_')}.csv`;
  document.body.appendChild(a); a.click(); document.body.removeChild(a);
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

// ===== Buying Signals =====
function renderSignalsBanner() {
  const b = document.getElementById("sigDemoBanner");
  if (SIGNALS._demo) {
    b.innerHTML = `<b>Demo dataset.</b> ${SIGNALS._demo_note || ""} `
      + `Today is anchored to ${SIGNALS.today}; signals decay with a `
      + `${SIGNALS.halflife_days}-day half-life and drop off after `
      + `${SIGNALS.dropoff_days} days.`;
  } else {
    b.style.display = "none";
  }
}

function signalMatchesIcp(s) {
  if (ui.sigIcp === "all") return true;
  // Always include statewide / vendor-wide signals — they don't have a
  // muni population, so the ICP filter shouldn't drop them.
  if (s.state === "ALL" || (s.population || 0) === 0) return true;
  const pop = s.population;
  if (ui.sigIcp === "sub15k")  return pop < 15000;
  if (ui.sigIcp === "under50k") return pop < 50000;
  return true;
}

function filteredSignals() {
  const q = ui.sigSearch.toLowerCase();
  return SIGNALS.signals.filter(s => {
    if (ui.sigType !== "all" && s.type !== ui.sigType) return false;
    if (ui.sigSev !== "all" && s.severity !== ui.sigSev) return false;
    if (!signalMatchesIcp(s)) return false;
    if (ui.sigStateFilter && s.state !== ui.sigStateFilter && s.state !== "ALL") return false;
    if (q && !(s.muni.toLowerCase().includes(q) || s.headline.toLowerCase().includes(q))) return false;
    return true;
  });
}

function renderSigKpis() {
  const all = SIGNALS.signals;
  const filt = filteredSignals();
  const high = filt.filter(s => s.severity === "high").length;
  const totalScore = filt.reduce((a, s) => a + s.score, 0);
  // hottest state
  const stScore = {};
  all.forEach(s => {
    if (s.state === "ALL") return;
    stScore[s.state] = (stScore[s.state] || 0) + s.score;
  });
  let hot = ["—", 0];
  Object.entries(stScore).forEach(([k, v]) => { if (v > hot[1]) hot = [k, v]; });

  const kpis = [
    {label: "Active signals", value: fmtInt(filt.length), sub: `of ${fmtInt(all.length)} total`},
    {label: "High severity", value: fmtInt(high), sub: "filtered"},
    {label: "Aggregate score", value: totalScore.toFixed(1), sub: "weighted by recency"},
    {label: "Hottest state", value: hot[0], sub: STATE_NAMES[hot[0]] || ""},
  ];
  document.getElementById("sigKpis").innerHTML =
    kpis.map(k => `<div class="kpi"><div class="label">${k.label}</div><div class="value">${k.value}</div><div class="sub">${k.sub}</div></div>`).join("");
}

function renderSigTypeChips() {
  const c = document.getElementById("sigTypeChips");
  const types = SIGNALS.types;
  let html = `<button class="btn chip-stype${ui.sigType === 'all' ? ' active' : ''}" data-stype="all">All</button>`;
  Object.entries(types).forEach(([k, v]) => {
    const active = ui.sigType === k ? " active" : "";
    html += `<button class="btn chip-stype${active}" data-stype="${k}" style="border-color:${v.color}${ui.sigType === k ? '' : '40'}">${v.label}</button>`;
  });
  c.innerHTML = html;
  c.querySelectorAll(".chip-stype").forEach(b => b.addEventListener("click", () => {
    ui.sigType = b.dataset.stype;
    renderSignalsTab();
  }));
}

function renderSignalsTile() {
  // Sum filtered scores per state
  const stScore = {};
  STATES.forEach(s => stScore[s] = 0);
  filteredSignals().forEach(s => {
    if (s.state === "ALL") {
      // statewide signal — distribute thinly across all states
      STATES.forEach(st => stScore[st] += s.score / STATES.length);
    } else if (stScore[s.state] !== undefined) {
      stScore[s.state] += s.score;
    }
  });
  let max = 0;
  STATES.forEach(s => { if (stScore[s] > max) max = stScore[s]; });
  if (max === 0) max = 1;

  const c = document.getElementById("tileSignals");
  c.innerHTML = "";
  const grid = document.createElement("div");
  grid.className = "tilemap";
  TILEMAP.forEach(row => row.forEach(st => {
    const tile = document.createElement("div");
    tile.className = "tile" + (st === "" ? " empty" : "");
    if (st !== "") {
      const v = stScore[st] || 0;
      const t = Math.pow(v / max, 0.55);
      tile.style.background = `rgba(239,68,68,${0.15 + t * 0.85})`;
      tile.style.color = "#fff";
      tile.innerHTML = `<div>${st}</div><div class="v">${v > 0.5 ? v.toFixed(1) : ""}</div>`;
      tile.title = `${STATE_NAMES[st]}: score ${v.toFixed(2)}`;
      if (ui.sigStateFilter === st) tile.classList.add("selected");
      tile.addEventListener("click", () => {
        ui.sigStateFilter = (ui.sigStateFilter === st) ? null : st;
        renderSignalsTab();
      });
    }
    grid.appendChild(tile);
  }));
  c.appendChild(grid);

  document.getElementById("sigMapTitle").textContent =
    "Signal density by state" + (ui.sigStateFilter ? ` — filtered to ${ui.sigStateFilter}` : "");
}

function renderActNow() {
  const c = document.getElementById("actNow");
  // Use top_acts but re-rank against current filter
  const filt = new Set(filteredSignals().map(s => s.id));
  const acts = SIGNALS.top_acts
    .map(a => {
      const matched = a.signals.filter(id => filt.has(id));
      const sum = matched.reduce((s, id) => s + (SIGNALS.signals.find(x => x.id === id)?.score || 0), 0);
      return {...a, matched, sum};
    })
    .filter(a => a.matched.length > 0)
    .sort((a, b) => b.sum - a.sum)
    .slice(0, 25);

  if (acts.length === 0) {
    c.innerHTML = '<div class="note">No accounts match current filters.</div>';
    return;
  }
  c.innerHTML = acts.map((a, i) => {
    const focusKey = a.muni + "|" + a.state;
    const focused = ui.sigFocusKey === focusKey ? " focused" : "";
    return `<div class="act-row${focused}" data-key="${focusKey}">
      <div class="rank">${i + 1}</div>
      <div>
        <div class="name">${a.muni}, ${a.state}</div>
        <div class="sub">${a.bucket}${a.population ? ' · ' + fmtInt(a.population) + ' pop' : ''}${a.incumbent ? ' · incumbent: ' + a.incumbent : ''}</div>
      </div>
      <div class="score">${a.sum.toFixed(2)}</div>
      <div class="count">${a.matched.length} signal${a.matched.length === 1 ? '' : 's'}</div>
    </div>`;
  }).join("");
  c.querySelectorAll(".act-row").forEach(el => {
    el.addEventListener("click", () => {
      ui.sigFocusKey = (ui.sigFocusKey === el.dataset.key) ? null : el.dataset.key;
      renderActNow();
      renderSignalsFeed();
    });
  });
}

function renderSignalsFeed() {
  let signals = filteredSignals();
  if (ui.sigFocusKey) {
    const [m, s] = ui.sigFocusKey.split("|");
    signals = signals.filter(x => x.muni === m && x.state === s);
  }
  signals.sort((a, b) => b.score - a.score);

  const c = document.getElementById("sigFeed");
  if (signals.length === 0) {
    c.innerHTML = '<div class="note">No signals match the current filter.</div>';
  } else {
    c.innerHTML = signals.map(s => {
      const meta = SIGNALS.types[s.type];
      const expires = s.expires ? ` · expires ${s.expires}` : '';
      return `<div class="sig-card sig-sev-${s.severity}">
        <div>
          <span class="badge" style="background:${meta.color}">${meta.label}</span>
        </div>
        <div>
          <div class="headline">${s.headline}</div>
          <div class="meta-line">
            <strong>${s.muni}, ${s.state}</strong>
            ${s.population ? ' · ' + fmtInt(s.population) + ' pop' : ''}
            ${s.bucket && s.population ? ' · ' + s.bucket : ''}
            ${s.incumbent ? ' · incumbent: <strong>' + s.incumbent + '</strong>' : ''}
          </div>
          <div class="details">${s.details}</div>
          <div class="meta-line">
            ${s.source}${expires} · detected ${s.detected} · severity ${s.severity}
          </div>
        </div>
        <div class="right">
          <span class="score">${s.score.toFixed(2)}</span>
          score
        </div>
      </div>`;
    }).join("");
  }
  document.getElementById("sigFeedTitle").textContent =
    `Signal feed (${signals.length})` + (ui.sigFocusKey ? ` — focused on ${ui.sigFocusKey.replace('|', ', ')}` : '');
}

function exportSignalsCsv() {
  const sigs = filteredSignals();
  const cols = ["id", "muni", "state", "population", "bucket", "type",
                "severity", "detected", "expires", "headline", "details",
                "source", "url", "incumbent", "score"];
  const escape = v => {
    if (v === null || v === undefined) return "";
    const s = String(v).replace(/"/g, '""');
    return /[",\n]/.test(s) ? '"' + s + '"' : s;
  };
  const csv = [cols.join(",")]
    .concat(sigs.map(s => cols.map(c => escape(s[c])).join(",")))
    .join("\n");
  const blob = new Blob([csv], {type: "text/csv"});
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `buying_signals_${SIGNALS.today}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function renderSignalsTab() {
  renderSigKpis();
  renderSigTypeChips();
  renderSignalsTile();
  renderActNow();
  renderSignalsFeed();
}

// ===== Top Prospects (greenfield) =====
function gfStatusClass(s) { return "gf-status gf-status-" + (s || "unknown").replace(/[^a-z]/g, ""); }
function gfScoreClass(n) { return n >= 60 ? "gf-score-strong" : n >= 50 ? "gf-score-mid" : "gf-score-weak"; }

function renderGfKpis() {
  const all = GREENFIELD.top_prospects;
  const filt = filteredProspects();
  const top = filt[0];
  const inWindow = filt.filter(p => p.renewal_status === "in-window" || p.renewal_status === "imminent").length;
  const greenfield = filt.filter(p => p.renewal_status === "greenfield").length;

  const totalAcv = filt.reduce((a, p) => a + (p.acv_mid || 0), 0);
  const kpis = [
    {label: "Top prospects shown", value: fmtInt(filt.length), sub: `of ${fmtInt(all.length)} cap (top ${fmtInt(GREENFIELD.total_scored)} scored)`},
    {label: "Top score", value: top ? top.score : "—", sub: top ? `${top.muni}, ${top.state}` : ""},
    {label: "Filtered ACV pool", value: fmtUsd(totalAcv), sub: "annual SaaS / maintenance"},
    {label: "In renewal window", value: fmtInt(inWindow), sub: "filtered subset"},
    {label: "Pure greenfield", value: fmtInt(greenfield), sub: "no incumbent on record"},
  ];
  document.getElementById("gfKpis").innerHTML =
    kpis.map(k => `<div class="kpi"><div class="label">${k.label}</div><div class="value">${k.value}</div><div class="sub">${k.sub}</div></div>`).join("");
}

function fillGfSelectors() {
  const s = document.getElementById("gfState");
  if (s.dataset.filled !== "1") {
    STATES.forEach(st => {
      const o = document.createElement("option");
      o.value = st; o.textContent = `${st} – ${STATE_NAMES[st]}`;
      s.appendChild(o);
    });
    s.dataset.filled = "1";
    s.addEventListener("change", () => { ui.gfState = s.value; renderProspectsTab(); });
  }
  const b = document.getElementById("gfBucket");
  if (b.dataset.filled !== "1") {
    [...BUCKETS, "small (<15K)"].forEach(bk => {
      const o = document.createElement("option");
      o.value = bk; o.textContent = bk;
      b.appendChild(o);
    });
    b.dataset.filled = "1";
    b.addEventListener("change", () => { ui.gfBucket = b.value; renderProspectsTab(); });
  }
  const search = document.getElementById("gfSearch");
  if (search.dataset.filled !== "1") {
    search.dataset.filled = "1";
    search.addEventListener("input", () => { ui.gfSearch = search.value.toLowerCase(); renderProspectsTab(); });
  }
}

function filteredProspects() {
  const q = ui.gfSearch;
  return GREENFIELD.top_prospects.filter(p => {
    if (ui.gfState !== "all" && p.state !== ui.gfState) return false;
    if (ui.gfBucket !== "all" && p.bucket !== ui.gfBucket) return false;
    if (ui.gfStatus !== "all" && p.renewal_status !== ui.gfStatus) return false;
    if (q) {
      const v = (p.incumbent && p.incumbent.vendor) || "";
      if (!p.muni.toLowerCase().includes(q)
          && !v.toLowerCase().includes(q)
          && !p.state.toLowerCase().includes(q)) return false;
    }
    return true;
  });
}

function renderGfList() {
  const t = document.getElementById("gfList");
  const filt = filteredProspects();
  document.getElementById("gfListTitle").textContent =
    `Top prospects (${filt.length})`;

  if (filt.length === 0) {
    t.innerHTML = "<thead><tr><th>—</th></tr></thead><tbody><tr><td>No prospects match the filter.</td></tr></tbody>";
    return;
  }
  let html = '<thead><tr><th>#</th><th>Score</th><th>Muni</th><th>State</th><th>Bucket</th><th>Incumbent</th><th>Renewal</th><th>Est. ACV</th><th>Top buyer</th></tr></thead><tbody>';
  filt.slice(0, 500).forEach((p, i) => {
    const inc = p.incumbent ? `${p.incumbent.vendor}${p.incumbent.product ? ' · ' + p.incumbent.product : ''}` : '<span style="color:#34d399">GREENFIELD</span>';
    const buyer = (p.personas && p.personas[0]) || "—";
    const acvStr = p.acv_mid ? `${fmtUsd(p.acv_mid)}<div style="font-size:9px;color:var(--muted)">${fmtUsd(p.acv_low)}–${fmtUsd(p.acv_high)}</div>` : "—";
    const key = p.muni + "|" + p.state;
    const focused = ui.gfFocusKey === key ? " focused" : "";
    html += `<tr class="gf-row${focused}" data-key="${key}">
      <td>${i + 1}</td>
      <td><span class="gf-score ${gfScoreClass(p.score)}">${p.score}</span></td>
      <td><strong>${p.muni}</strong></td>
      <td>${p.state}</td>
      <td>${p.bucket || "—"}</td>
      <td>${inc}</td>
      <td><span class="${gfStatusClass(p.renewal_status)}">${p.renewal_status}</span></td>
      <td>${acvStr}</td>
      <td>${buyer}</td>
    </tr>`;
  });
  if (filt.length > 500) {
    html += `<tr><td colspan="9" style="text-align:center;color:var(--muted);font-size:11px">... ${filt.length - 500} more (use filters or CSV export)</td></tr>`;
  }
  html += "</tbody>";
  t.innerHTML = html;
  t.querySelectorAll(".gf-row").forEach(row => {
    row.addEventListener("click", () => {
      ui.gfFocusKey = row.dataset.key;
      renderGfList();
      renderGfDetail();
    });
  });
}

function renderGfDetail() {
  const c = document.getElementById("gfDetail");
  if (!ui.gfFocusKey) {
    document.getElementById("gfDetailTitle").textContent = "Click a row for details";
    c.innerHTML = '<div class="note">Pick a prospect on the left to see score breakdown, personas, and outreach hints.</div>';
    return;
  }
  const [muni, state] = ui.gfFocusKey.split("|");
  const p = GREENFIELD.top_prospects.find(x => x.muni === muni && x.state === state);
  if (!p) {
    c.innerHTML = '<div class="note">Prospect not found in current cache.</div>';
    return;
  }
  document.getElementById("gfDetailTitle").innerHTML =
    `${p.muni}, ${p.state} <span style="color:var(--muted);font-size:12px;font-weight:400">· score ${p.score} · ${p.bucket}${p.pop ? ' · ' + fmtInt(p.pop) + ' pop' : ''}</span>`;

  const comps = p.components;
  const max = {icp: 30, displace: 25, signal: 25, white_space: 20, renewal: 10};
  const compRow = (label, key) => {
    const v = comps[key], m = max[key];
    return `<div class="gf-component"><span>${label}</span><div class="gf-bar"><div class="gf-bar-fill" style="width:${(v/m)*100}%"></div></div><span style="font-weight:600">${v}/${m}</span></div>`;
  };

  let inc = "—";
  if (p.incumbent) {
    const sinceStr = p.incumbent.since ? ` (since ${p.incumbent.since})` : "";
    inc = `<strong>${p.incumbent.vendor}</strong>${p.incumbent.product ? ' · ' + p.incumbent.product : ''}${sinceStr}`;
  } else {
    inc = '<strong style="color:#34d399">GREENFIELD</strong> — no incumbent on record';
  }

  const renewalBlock = p.renewal_label
    ? `<div class="gf-detail-section"><h4>Renewal</h4>
        <span class="${gfStatusClass(p.renewal_status)}">${p.renewal_status}</span>
        <div class="note" style="margin-top:4px">${p.renewal_label}</div>
       </div>`
    : "";

  const personasHtml = (p.personas || []).map(t =>
    `<div class="gf-persona"><span>${t}</span></div>`).join("")
    || '<div class="note">no personas mapped</div>';

  const dirHints = (GREENFIELD.directory_hints_by_state[p.state] || []);
  const dirHtml = dirHints.length
    ? dirHints.map(d => `<div class="gf-persona"><a href="${d.url}" target="_blank" rel="noopener">${d.label}</a></div>`).join("")
    : '<div class="note">no directory links</div>';

  const acvBlock = p.acv_mid ? `
    <div class="gf-detail-section">
      <h4>Estimated ACV (annual)</h4>
      <div style="display:flex;gap:14px;align-items:baseline">
        <span style="font-size:18px;font-weight:700;color:var(--accent)">${fmtUsd(p.acv_mid)}</span>
        <span style="color:var(--muted);font-size:11px">${fmtUsd(p.acv_low)} – ${fmtUsd(p.acv_high)}</span>
      </div>
      <div class="note" style="margin-top:4px">+ ${fmtUsd(p.acv_impl)} typical implementation (one-off)</div>
    </div>` : "";

  c.innerHTML = `
    <div class="gf-detail-section">
      <h4>Incumbent</h4>
      ${inc}
    </div>
    ${renewalBlock}
    ${acvBlock}
    <div class="gf-detail-section">
      <h4>Score breakdown (${p.score}/100)</h4>
      ${compRow("ICP fit", "icp")}
      ${compRow("Displaceability", "displace")}
      ${compRow("Signal intensity", "signal")}
      ${compRow("White space", "white_space")}
      ${compRow("Renewal boost", "renewal")}
    </div>
    <div class="gf-detail-section">
      <h4>Likely buyers (top titles for this size + product)</h4>
      ${personasHtml}
    </div>
    <div class="gf-detail-section">
      <h4>Where to find contacts</h4>
      ${dirHtml}
    </div>
  `;
}

function exportGfCsv() {
  const rows = filteredProspects();
  const cols = ["score", "muni", "state", "pop", "bucket", "incumbent_vendor",
                 "incumbent_product", "incumbent_since", "renewal_status",
                 "renewal_label", "next_renewal_min", "next_renewal_max",
                 "acv_low", "acv_mid", "acv_high", "acv_impl",
                 "primary_buyer", "secondary_buyer", "tertiary_buyer",
                 "icp", "displace", "signal", "white_space", "renewal_boost"];
  const escape = v => {
    if (v === null || v === undefined) return "";
    const s = String(v).replace(/"/g, '""');
    return /[",\n]/.test(s) ? '"' + s + '"' : s;
  };
  const out = [cols.join(",")];
  rows.forEach(p => {
    const inc = p.incumbent || {};
    const personas = p.personas || [];
    const c = p.components || {};
    out.push([
      p.score, p.muni, p.state, p.pop, p.bucket,
      inc.vendor, inc.product, inc.since,
      p.renewal_status, p.renewal_label,
      p.next_renewal_min, p.next_renewal_max,
      p.acv_low, p.acv_mid, p.acv_high, p.acv_impl,
      personas[0], personas[1], personas[2],
      c.icp, c.displace, c.signal, c.white_space, c.renewal,
    ].map(escape).join(","));
  });
  const blob = new Blob([out.join("\n")], {type: "text/csv"});
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = `top_prospects_${GREENFIELD.today}.csv`;
  document.body.appendChild(a); a.click(); document.body.removeChild(a);
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function renderProspectsTab() {
  fillGfSelectors();
  renderGfKpis();
  renderGfList();
  renderGfDetail();
}

// ===== Wire up controls =====
document.querySelectorAll("[data-metric]").forEach(b => b.addEventListener("click", () => {
  document.querySelectorAll("[data-metric]").forEach(x => x.classList.remove("active"));
  b.classList.add("active"); ui.metric = b.dataset.metric; renderOverview();
}));
document.querySelectorAll(".chip-type").forEach(b => b.addEventListener("click", () => {
  document.querySelectorAll(".chip-type").forEach(x => x.classList.remove("active"));
  b.classList.add("active"); ui.type = b.dataset.type; renderOverview();
}));
document.querySelectorAll(".chip-htype").forEach(b => b.addEventListener("click", () => {
  document.querySelectorAll(".chip-htype").forEach(x => x.classList.remove("active"));
  b.classList.add("active"); ui.htype = b.dataset.type; renderHeatmaps();
}));
document.querySelectorAll("[data-vmap]").forEach(b => b.addEventListener("click", () => {
  document.querySelectorAll("[data-vmap]").forEach(x => x.classList.remove("active"));
  b.classList.add("active"); ui.vmap = b.dataset.vmap; renderVendorMap();
}));
document.querySelectorAll("[data-smallm]").forEach(b => b.addEventListener("click", () => {
  document.querySelectorAll("[data-smallm]").forEach(x => x.classList.remove("active"));
  b.classList.add("active"); ui.smallm = b.dataset.smallm; renderSmallMultiples();
}));
document.querySelectorAll(".chip-cmetric").forEach(b => b.addEventListener("click", () => {
  document.querySelectorAll(".chip-cmetric").forEach(x => x.classList.remove("active"));
  b.classList.add("active"); ui.cMetric = b.dataset.cmetric; renderChoropleth();
}));
document.querySelectorAll(".chip-mshow").forEach(b => b.addEventListener("click", () => {
  document.querySelectorAll(".chip-mshow").forEach(x => x.classList.remove("active"));
  b.classList.add("active"); ui.mShow = b.dataset.mshow; renderLists();
}));
document.getElementById("namesExport").addEventListener("click", exportNamesCsv);
document.getElementById("namedCustExport").addEventListener("click", exportNamedCustomersCsv);
document.getElementById("namedCustSearch").addEventListener("input", e => {
  ui.ncSearch = e.target.value;
  renderNamedCustomers();
});
document.querySelectorAll(".chip-gfstatus").forEach(b => b.addEventListener("click", () => {
  document.querySelectorAll(".chip-gfstatus").forEach(x => x.classList.remove("active"));
  b.classList.add("active"); ui.gfStatus = b.dataset.gfstatus; renderProspectsTab();
}));
document.getElementById("gfExport").addEventListener("click", exportGfCsv);
document.getElementById("nameSearch").addEventListener("input", renderLists);

document.querySelectorAll(".chip-sev").forEach(b => b.addEventListener("click", () => {
  document.querySelectorAll(".chip-sev").forEach(x => x.classList.remove("active"));
  b.classList.add("active"); ui.sigSev = b.dataset.sev; renderSignalsTab();
}));
document.querySelectorAll(".chip-sicp").forEach(b => b.addEventListener("click", () => {
  document.querySelectorAll(".chip-sicp").forEach(x => x.classList.remove("active"));
  b.classList.add("active"); ui.sigIcp = b.dataset.sicp; renderSignalsTab();
}));
document.getElementById("sigSearch").addEventListener("input", e => {
  ui.sigSearch = e.target.value;
  renderSignalsTab();
});
document.getElementById("sigExport").addEventListener("click", exportSignalsCsv);

// ===== Initial render =====
updateHeaderSummary();
renderOverview();
renderHeatmaps();
renderNamesTile();
renderVendorCards();
renderVendorMap();
renderVendorTopChart();
renderMatrix();
renderSmallMultiples();
renderNamedCustomers();
renderChoropleth();
renderSignalsBanner();
renderSignalsTab();
renderProspectsTab();

// Auto-select biggest state for names tab so it's not empty
selectState(STATES.map(s => [s, TAM.states[s].total_entities]).sort((a,b) => b[1]-a[1])[0][0]);
</script>
</body>
</html>
"""


if __name__ == "__main__":
    build()
