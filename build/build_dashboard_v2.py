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
NAMES_JSON = os.path.join(HERE, "names_data.json")
HTML_PATH = os.path.join(OUT_DIR, "Local_Government_TAM_Dashboard.html")


def build():
    with open(TAM_JSON) as f:
        tam = json.load(f)
    with open(COMP_JSON) as f:
        comp = json.load(f)
    with open(NAMES_JSON) as f:
        names = json.load(f)

    # Stringify safely for inline embedding
    tam_s = json.dumps(tam, separators=(",", ":"))
    comp_s = json.dumps(comp, separators=(",", ":"))
    names_s = json.dumps(names, separators=(",", ":"))
    tile_s = json.dumps(TILE_MAP)

    html = HTML_TEMPLATE.replace("__TAM__", tam_s)\
                        .replace("__COMP__", comp_s)\
                        .replace("__NAMES__", names_s)\
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
</nav>

<main>

<!-- ===== TAB 1: OVERVIEW ===== -->
<section class="tab active" id="tab-overview">
  <div class="controls">
    <label>Metric:</label>
    <button class="btn active" data-metric="spend">Spend ($)</button>
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
  <div class="controls">
    <label>Filter type:</label>
    <button class="btn chip-htype active" data-type="all">All (excl. SD)</button>
    <button class="btn chip-htype" data-type="munis">Municipalities</button>
    <button class="btn chip-htype" data-type="counties">Counties</button>
    <button class="btn chip-htype" data-type="townships">Townships</button>
  </div>
  <div class="grid row2">
    <div class="card">
      <h3>Entity Count Heatmap</h3>
      <div class="scroll"><table class="heatmap" id="heatmapCount"></table></div>
      <div class="note">Cells colored per-column on a log-scaled percentile.</div>
    </div>
    <div class="card">
      <h3>Estimated Annual Spend Heatmap</h3>
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
      <div class="note">Click any state tile to load its counties and cities.</div>
    </div>
    <div class="card">
      <h3 id="namesHeader">No state selected</h3>
      <div class="controls" style="margin-bottom:8px">
        <input class="search" id="nameSearch" placeholder="Search counties or cities&hellip;">
      </div>
      <div class="controls" id="bucketChips" style="margin-top:0">
        <label>Bucket:</label>
      </div>
      <div class="grid row2">
        <div>
          <h4 style="font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.5px;margin:8px 0 6px">Counties</h4>
          <div class="list" id="countyList"></div>
        </div>
        <div>
          <h4 style="font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.5px;margin:8px 0 6px">Cities (&ge;15K pop)</h4>
          <div class="list" id="cityList"></div>
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
    <h3>Full vendor &times; state matrix</h3>
    <div class="scroll"><table class="matrix" id="matrix"></table></div>
  </div>
</section>

</main>

<script>
const TAM = __TAM__;
const COMP = __COMP__;
const NAMES = __NAMES__;
const TILEMAP = __TILEMAP__;

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
};

// ===== Tabs =====
document.querySelectorAll("nav.tabs button").forEach(b => {
  b.addEventListener("click", () => {
    document.querySelectorAll("nav.tabs button").forEach(x => x.classList.remove("active"));
    b.classList.add("active");
    document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
    document.getElementById("tab-" + b.dataset.tab).classList.add("active");
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
function metricVal(st) {
  return ui.metric === "spend" ? spendVal(st, ui.type) : entityCount(st, ui.type);
}

// ===== Header summary =====
function updateHeaderSummary() {
  const totalSpend = STATES.reduce((s, st) => s + TAM.states[st].total_spend, 0);
  const totalEntities = STATES.reduce((s, st) => s + TAM.states[st].total_entities, 0);
  const totalCustomers = Object.values(COMP.vendors).reduce((s, v) => s + v.allocated, 0);
  document.getElementById("hdrSummary").innerHTML =
    "TAM " + fmtUsd(totalSpend) + " &middot; "
    + fmtInt(totalEntities) + " entities &middot; "
    + fmtInt(totalCustomers) + " tracked customers";
}

// ===== KPIs =====
function renderKpis() {
  const totalSpend = STATES.reduce((s, st) => s + spendVal(st, ui.type), 0);
  const totalCount = STATES.reduce((s, st) => s + entityCount(st, ui.type), 0);
  const sorted = STATES.map(st => [st, metricVal(st)]).sort((a,b) => b[1]-a[1]);
  const top1 = sorted[0];
  const top5Share = sorted.slice(0, 5).reduce((s,x) => s + x[1], 0) /
                    sorted.reduce((s,x) => s + x[1], 0);

  const kpis = [
    {label: "Total TAM (operating spend)", value: fmtUsd(totalSpend), sub: "annual, 2022 baseline"},
    {label: "Total entities", value: fmtInt(totalCount), sub: ui.type === "all" ? "all types" : "selected type"},
    {label: "Largest state",   value: top1[0] + " &middot; " + (ui.metric === "spend" ? fmtUsd(top1[1]) : fmtInt(top1[1])), sub: STATE_NAMES[top1[0]]},
    {label: "Top-5 state share", value: fmtPct(top5Share), sub: "of " + (ui.metric === "spend" ? "spend" : "entities")},
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
  charts.topStates = new Chart(ctx, {
    type: "bar",
    data: { labels: sorted.map(x => x[0]),
            datasets: [{ data: sorted.map(x => x[1]),
                         backgroundColor: "#38bdf8" }] },
    options: { indexAxis: "y", responsive: true, maintainAspectRatio: false,
               plugins: { legend: { display: false },
                          tooltip: { callbacks: { label: (c) => ui.metric === "spend" ? fmtUsd(c.parsed.x) : fmtInt(c.parsed.x) } } },
               scales: { x: { ticks: { color: "#94a3b8", callback: v => ui.metric === "spend" ? fmtUsd(v) : fmtInt(v) }, grid: { color: "#334155" } },
                         y: { ticks: { color: "#e2e8f0" }, grid: { display: false } } } }
  });
}

function renderEntityTypeChart() {
  destroyChart("entityType");
  const types = ["counties", "munis", "townships", "special_districts"];
  const labels = ["Counties", "Munis", "Townships", "Special Districts"];
  const values = types.map(t => STATES.reduce((s, st) => s + (ui.metric === "spend" ? spendVal(st, t) : entityCount(st, t)), 0));
  const ctx = document.getElementById("entityTypeChart").getContext("2d");
  charts.entityType = new Chart(ctx, {
    type: "doughnut",
    data: { labels, datasets: [{ data: values, backgroundColor: ["#38bdf8", "#a855f7", "#10b981", "#f59e0b"], borderColor: "#1e293b", borderWidth: 2 }] },
    options: { responsive: true, maintainAspectRatio: false,
               plugins: { legend: { position: "bottom", labels: { color: "#e2e8f0", font: { size: 11 } } },
                          tooltip: { callbacks: { label: (c) => c.label + ": " + (ui.metric === "spend" ? fmtUsd(c.parsed) : fmtInt(c.parsed)) } } } }
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
        else total += TAM.states[st].by_bucket[t][i];
      });
    });
    return total;
  });
  const ctx = document.getElementById("bucketChart").getContext("2d");
  charts.bucket = new Chart(ctx, {
    type: "bar",
    data: { labels: BUCKETS, datasets: [{ data: values, backgroundColor: "#a855f7" }] },
    options: { responsive: true, maintainAspectRatio: false,
               plugins: { legend: { display: false },
                          tooltip: { callbacks: { label: (c) => ui.metric === "spend" ? fmtUsd(c.parsed.y) : fmtInt(c.parsed.y) } } },
               scales: { x: { ticks: { color: "#e2e8f0" }, grid: { display: false } },
                         y: { ticks: { color: "#94a3b8", callback: v => ui.metric === "spend" ? fmtUsd(v) : fmtInt(v) }, grid: { color: "#334155" } } } }
  });
}

function renderOverview() {
  renderKpis();
  renderTileMap("tileOverview", metricVal, {
    color: "30,58,138",
    label: v => ui.metric === "spend" ? fmtUsd(v) : fmtInt(v),
    tip: v => ui.metric === "spend" ? fmtUsd(v) : fmtInt(v),
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
  // Keep label, replace chips
  c.innerHTML = '<label>Bucket:</label>';
  ["all", ...BUCKETS].forEach(b => {
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
function renderLists() {
  if (!ui.selectedState) return;
  const st = ui.selectedState;
  const data = NAMES[st] || { counties: [], cities: [] };
  const q = (document.getElementById("nameSearch").value || "").toLowerCase();

  const cl = document.getElementById("countyList");
  cl.innerHTML = data.counties
    .filter(c => !q || c.name.toLowerCase().includes(q))
    .map(c => `<div class="item"><span class="name">${c.name}</span><span class="meta">${c.fips || ""}</span></div>`)
    .join("") || '<div class="item"><span class="name">No counties</span></div>';

  const cityList = document.getElementById("cityList");
  let cities = data.cities;
  if (ui.selectedBucket !== "all") cities = cities.filter(c => c.bucket === ui.selectedBucket);
  if (q) cities = cities.filter(c => c.name.toLowerCase().includes(q));
  cityList.innerHTML = cities
    .map(c => `<div class="item"><span class="name">${c.name}</span><span class="meta">${fmtInt(c.pop)} &middot; ${c.bucket}</span></div>`)
    .join("") || '<div class="item"><span class="name">No cities &ge;15K</span></div>';
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
function renderMatrix() {
  const t = document.getElementById("matrix");
  const vendors = Object.keys(COMP.vendors);
  let html = "<thead><tr><th>State</th>" +
    vendors.map(v => `<th>${v}</th>`).join("") +
    "<th>Combined</th><th>Pen %</th></tr></thead><tbody>";
  STATES.forEach(st => {
    const addr = COMP.addressable_by_state[st] || 1;
    const combined = vendors.reduce((s, v) => s + (COMP.vendors[v].by_state[st] || 0), 0);
    const pen = combined / addr;
    html += "<tr><td>" + st + "</td>" +
      vendors.map(v => `<td>${fmtInt(COMP.vendors[v].by_state[st] || 0)}</td>`).join("") +
      `<td style="font-weight:600">${fmtInt(combined)}</td><td style="font-weight:600">${(pen * 100).toFixed(2)}%</td></tr>`;
  });
  html += "</tbody>";
  t.innerHTML = html;
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
document.getElementById("nameSearch").addEventListener("input", renderLists);

// ===== Initial render =====
updateHeaderSummary();
renderOverview();
renderHeatmaps();
renderNamesTile();
renderVendorCards();
renderVendorMap();
renderVendorTopChart();
renderMatrix();

// Auto-select biggest state for names tab so it's not empty
selectState(STATES.map(s => [s, TAM.states[s].total_entities]).sort((a,b) => b[1]-a[1])[0][0]);
</script>
</body>
</html>
"""


if __name__ == "__main__":
    build()
