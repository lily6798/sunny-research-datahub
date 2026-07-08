#!/usr/bin/env python3
import json, re, math
import pandas as pd

NIELSEN_DIR = "/Users/lily/sunny-research-assets/data/nielsen"
OUT_DIR = "/Users/lily/sunny-research-assets/dashboards"

MONTHS_ORDER = ["August 2025","September 2025","October 2025","November 2025","December 2025",
                "January 2026","February 2026","March 2026","April 2026","May 2026","June 2026","July 2026"]
MONTH_LABELS = ["Aug","Sep","Oct","Nov","Dec","Jan","Feb","Mar","Apr","May","Jun","Jul*"]

CHANNEL_MAP = {
    "Social": "Social",
    "General Display": "Digital Display",
    "Metropolitan Television": "Television",
    "Regional Television": "Television",
    "Out of Home": "Out of Home",
    "Metropolitan Radio": "Radio",
    "Regional Radio (Creative)": "Radio",
    "Metropolitan Press": "Press",
    "Regional Press": "Press",
    "Magazines": "Magazines",
    "Cinema": "Cinema",
}

def load_raw(fname):
    df = pd.read_excel(f"{NIELSEN_DIR}/{fname}", header=None, skiprows=11)
    df.columns = ['advertiser','media_type','total','m1','m2','m3','m4','m5','m6','m7','m8','m9','m10','m11','m12']
    df = df[df['advertiser'].notna()].copy()
    df['channel'] = df['media_type'].map(CHANNEL_MAP)
    for c in ['total','m1','m2','m3','m4','m5','m6','m7','m8','m9','m10','m11','m12']:
        df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
    return df

def fmtM(v):
    return f"${v/1e6:.1f}M"

def fmt_dollar(v):
    return f"${round(v):,}"

def pct(v, t):
    return f"{v/t*100:.1f}%" if t else "0.0%"

def build(vertical):
    df = load_raw(vertical['file'])
    adv_rows = df[df['media_type'].isna()].copy()  # advertiser-level total rows
    adv_rows = adv_rows[adv_rows['advertiser'] != 'Grand Total']
    chan_rows = df[df['media_type'].notna() & df['channel'].notna()].copy()

    grand_total = float(adv_rows['total'].sum())
    n_advertisers = int((adv_rows['total'] > 0).sum())

    month_tot = [float(adv_rows[f'm{i+1}'].sum()) for i in range(12)]

    channel_tot = chan_rows.groupby('channel')['total'].sum().sort_values(ascending=False)
    channel = {k: float(v) for k, v in channel_tot.items()}
    n_channels = len(channel)

    channel_month = {}
    for ch in channel.keys():
        sub = chan_rows[chan_rows['channel'] == ch]
        channel_month[ch] = [float(sub[f'm{i+1}'].sum()) for i in range(12)]

    # per-advertiser channel breakdown for table/top list
    adv_names = adv_rows[adv_rows['total'] > 0].sort_values('total', ascending=False)

    def channels_for(name):
        sub = chan_rows[chan_rows['advertiser'] == name]
        out = {}
        for _, r in sub.iterrows():
            out[r['channel']] = out.get(r['channel'], 0) + float(r['total'])
        return {k: v for k, v in out.items() if v > 0}

    structure_fn = vertical['structure_fn']
    category_fn = vertical['category_fn']

    top_advertisers = []
    for _, r in adv_names.head(70).iterrows():
        name = r['advertiser']
        monthly = [float(r[f'm{i+1}']) for i in range(12)]
        top_advertisers.append({
            "advertiser": name,
            "total": float(r['total']),
            "segment": category_fn(name),
            "structure": structure_fn(name),
            "monthly": monthly,
            "channels": channels_for(name),
        })

    # aggregate structure & category across ALL advertisers (not just top 70)
    adv_names = adv_names.copy()
    adv_names['structure'] = adv_names['advertiser'].map(structure_fn)
    adv_names['segment'] = adv_names['advertiser'].map(category_fn)

    structure_tot = adv_names.groupby('structure')['total'].sum().sort_values(ascending=False)
    structure = {k: float(v) for k, v in structure_tot.items()}

    segment_tot = adv_names.groupby('segment')['total'].sum().sort_values(ascending=False)
    segment = {k: float(v) for k, v in segment_tot.items()}

    # segment_month: need per-segment monthly totals (adv_names already carries m1..m12)
    segment_month = {}
    for seg in segment.keys():
        sub = adv_names[adv_names['segment'] == seg]
        segment_month[seg] = [float(sub[f'm{i+1}'].sum()) for i in range(12)]

    # full list of every advertiser (not just the top 70), for the "All Advertisers" table
    chan_pivot = chan_rows.groupby(['advertiser', 'channel'])['total'].sum().reset_index()
    chan_pivot = chan_pivot.sort_values('total', ascending=False)
    top_chan_lookup = chan_pivot.drop_duplicates('advertiser')[['advertiser', 'channel', 'total']]
    top_chan_lookup = top_chan_lookup.rename(columns={'channel': 'top_channel', 'total': 'top_channel_total'})
    full_df = adv_names.merge(top_chan_lookup, on='advertiser', how='left')
    full_df['top_channel_pct'] = (full_df['top_channel_total'] / full_df['total']).fillna(0)

    full_list = []
    for _, r in full_df.iterrows():
        full_list.append({
            "advertiser": r['advertiser'],
            "total": float(r['total']),
            "segment": r['segment'],
            "structure": r['structure'],
            "top_channel": r['top_channel'] if pd.notna(r['top_channel']) else "—",
            "top_channel_pct": round(float(r['top_channel_pct']), 4),
        })

    DATA = {
        "grand_total": grand_total,
        "n_advertisers": n_advertisers,
        "n_channels": n_channels,
        "months": MONTH_LABELS,
        "month_tot": month_tot,
        "channel": channel,
        "channel_month": channel_month,
        "segment": segment,
        "segment_month": segment_month,
        "structure": structure,
        "top_advertisers": top_advertisers,
        "full_list": full_list,
    }

    # ---- derived numbers for KPIs / insights (computed in Python, static) ----
    t0 = top_advertisers[0]
    top10_sum = sum(a['total'] for a in top_advertisers[:10])
    top_channel_name, top_channel_val = list(channel.items())[0]
    kpi_structure_val = structure.get(vertical['struct_kpi_key'], 0)

    pk_i = month_tot[:11].index(max(month_tot[:11]))
    tr_i = month_tot[:11].index(min(month_tot[:11]))
    swing_pct = round((month_tot[pk_i] / month_tot[tr_i] - 1) * 100) if month_tot[tr_i] else 0

    kpis = [
        {"v": fmtM(grand_total), "l": "Total measured spend"},
        {"v": t0['advertiser'], "l": "#1 spender", "d": f"{fmtM(t0['total'])} · {pct(t0['total'], grand_total)}"},
        {"v": pct(top10_sum, grand_total), "l": "Captured by top 10 advertisers"},
        {"v": pct(top_channel_val, grand_total), "l": f"{top_channel_name} share (largest channel)", "d": fmtM(top_channel_val)},
        {"v": pct(kpi_structure_val, grand_total), "l": vertical['struct_kpi_label'], "d": fmtM(kpi_structure_val)},
    ]

    struct_note = vertical['struct_note_fn'](structure, grand_total, fmtM, pct)

    insights = vertical['insights_fn'](dict(
        grand_total=grand_total, n_advertisers=n_advertisers, channel=channel, structure=structure,
        segment=segment, top_advertisers=top_advertisers, months=MONTH_LABELS, month_tot=month_tot,
        pk_i=pk_i, tr_i=tr_i, swing_pct=swing_pct, top10_sum=top10_sum, t0=t0,
        fmtM=fmtM, pct=pct,
    ))

    DATA['kpis'] = kpis
    DATA['struct_note'] = struct_note
    DATA['insights'] = insights

    return DATA


TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{page_title}</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
  :root{{
    --bg:#FBFBFB; --panel:#FFFFFF; --panel2:#F3F3F3; --line:#E4E4E4;
    --ink:#0A0A0A; --muted:#585858; --accent:#FDB600; --accent2:#C98A00; --grey:#585858;
  }}
  *{{box-sizing:border-box}}
  body{{margin:0;background:var(--bg);color:var(--ink);
    font-family:'Poppins',-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;font-weight:300;line-height:1.5}}
  .wrap{{max-width:1280px;margin:0 auto;padding:28px 28px 80px}}
  .brandbar{{display:flex;justify-content:space-between;align-items:center;border-bottom:2px solid var(--accent);
    padding-bottom:16px;margin-bottom:26px}}
  .wordmark{{font-weight:700;font-size:22px;letter-spacing:.5px;text-transform:uppercase}}
  .wordmark .dot{{color:var(--accent)}}
  .brandbar .tagline{{color:var(--accent);font-weight:600;font-size:11px;letter-spacing:2.5px;text-transform:uppercase}}
  header.top{{display:flex;justify-content:space-between;align-items:flex-end;flex-wrap:wrap;gap:16px;margin-bottom:8px}}
  h1{{font-size:27px;margin:0;letter-spacing:-.3px;font-weight:700;text-transform:uppercase}}
  .sub{{color:var(--muted);font-size:13px;margin-top:7px;font-weight:300}}
  .tag{{display:inline-block;background:var(--panel2);border:1px solid var(--line);color:var(--muted);
    font-size:11px;padding:4px 10px;border-radius:20px;margin-top:10px}}
  .kpis{{display:grid;grid-template-columns:repeat(5,1fr);gap:14px;margin:24px 0 8px}}
  .kpi{{background:var(--panel);border:1px solid var(--line);border-top:3px solid var(--accent);border-radius:14px;padding:16px 18px;box-shadow:0 1px 5px rgba(0,0,0,.05)}}
  .kpi .v{{font-size:26px;font-weight:700;letter-spacing:-.5px}}
  .kpi .l{{color:var(--muted);font-size:12px;margin-top:4px;font-weight:300}}
  .kpi .d{{font-size:11px;margin-top:6px;color:var(--accent);font-weight:500}}
  .grid{{display:grid;gap:18px;margin-top:18px}}
  .g2{{grid-template-columns:1fr 1fr}}
  .g3{{grid-template-columns:1.4fr 1fr}}
  .card{{background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:20px 22px;position:relative;box-shadow:0 1px 5px rgba(0,0,0,.05)}}
  .card h3{{margin:0 0 2px;font-size:15px;font-weight:600;text-transform:uppercase;letter-spacing:.3px}}
  .dl{{position:absolute;top:16px;right:16px;background:var(--panel2);border:1px solid var(--line);
    color:var(--muted);font-size:11px;font-weight:600;padding:5px 11px;border-radius:8px;cursor:pointer;
    display:inline-flex;align-items:center;gap:5px;transition:.15s;z-index:5}}
  .dl:hover{{background:var(--accent);border-color:var(--accent);color:#000}}
  .card .cap{{color:var(--muted);font-size:12px;margin-bottom:14px;font-weight:300}}
  .chart-box{{position:relative;height:300px}}
  .chart-tall{{height:420px}}
  table{{width:100%;border-collapse:collapse;font-size:13px}}
  th,td{{text-align:left;padding:8px 10px;border-bottom:1px solid var(--line)}}
  th{{color:var(--muted);font-weight:600;font-size:11px;text-transform:uppercase;letter-spacing:.04em}}
  td.num,th.num{{text-align:right;font-variant-numeric:tabular-nums}}
  tr:hover td{{background:rgba(0,0,0,.03)}}
  .pill{{font-size:10.5px;padding:2px 8px;border-radius:10px;background:var(--panel2);border:1px solid var(--line);color:var(--muted);white-space:nowrap}}
  .bar-cell{{position:relative}}
  .bar-fill{{position:absolute;left:0;top:0;bottom:0;background:linear-gradient(90deg,rgba(253,182,0,.30),rgba(253,182,0,.06));border-radius:4px;z-index:0}}
  .bar-cell span{{position:relative;z-index:1}}
  .insights{{display:grid;grid-template-columns:repeat(2,1fr);gap:14px}}
  .ins{{background:var(--panel2);border:1px solid var(--line);border-left:3px solid var(--accent);border-radius:10px;padding:14px 16px}}
  .ins b{{color:var(--accent);font-weight:600}}
  .ins .h{{font-size:13px;font-weight:600;margin-bottom:4px;text-transform:uppercase;letter-spacing:.3px}}
  .ins p{{margin:0;font-size:12.5px;color:#3D3D3D;font-weight:300}}
  .note{{color:var(--muted);font-size:11.5px;margin-top:10px;font-style:italic;font-weight:300}}
  .seg{{display:flex;gap:6px;margin-bottom:14px;flex-wrap:wrap}}
  .seg button{{background:var(--panel2);border:1px solid var(--line);color:var(--muted);font-size:12px;
    padding:6px 12px;border-radius:8px;cursor:pointer;font-family:inherit;font-weight:400}}
  .seg button.on{{background:var(--accent);border-color:var(--accent);color:#000;font-weight:600}}
  footer{{color:var(--muted);font-size:11px;margin-top:40px;border-top:2px solid var(--accent);padding-top:16px;font-weight:300}}
  .back-link{{display:inline-flex;align-items:center;gap:6px;color:var(--muted);font-size:12px;font-weight:600;
    text-decoration:none;margin-bottom:16px;text-transform:uppercase;letter-spacing:.04em;transition:.15s}}
  .back-link:hover{{color:var(--accent2)}}
  @media(max-width:900px){{.kpis{{grid-template-columns:repeat(2,1fr)}}.g2,.g3{{grid-template-columns:1fr}}.insights{{grid-template-columns:1fr}}}}
</style>
</head>
<body>
<div class="wrap">
  <div class="brandbar">
    <div class="wordmark">SUNNY ADVERTISING<span class="dot">.</span></div>
    <div class="tagline">Your Media Performance Partners</div>
  </div>
  <a href="../index.html" class="back-link">&#x2190; All Research Assets</a>
  <header class="top">
    <div>
      <h1>{h1}</h1>
      <div class="sub">Measured advertising spend (rate-card est.), Aug 2025 – Jul 2026 (12-month rolling to 8 Jul 2026) · Nielsen Ad Intel categories</div>
      <span class="tag" id="tag-scope"></span>
    </div>
    <div style="text-align:right">
      <div class="sub">Total measured spend</div>
      <div style="font-size:30px;font-weight:800;letter-spacing:-.6px" id="hero-total"></div>
    </div>
  </header>

  <div class="kpis" id="kpis"></div>

  <div class="grid g2">
    <div class="card">
      <button class="dl" data-dl="struct">⬇ PNG</button>
      <h3>{struct_title}</h3>
      <div class="cap">{struct_cap}</div>
      <div class="chart-box"><canvas id="structChart"></canvas></div>
      <div class="note" id="struct-note"></div>
    </div>
    <div class="card">
      <button class="dl" data-dl="channel">⬇ PNG</button>
      <h3>Channel Mix</h3>
      <div class="cap">Total spend by media channel across all active {vertical_name} advertisers.</div>
      <div class="chart-box"><canvas id="channelChart"></canvas></div>
    </div>
  </div>

  <div class="grid">
    <div class="card">
      <button class="dl" data-dl="seas">⬇ PNG</button>
      <h3>Monthly Seasonality</h3>
      <div class="cap">Total spend by month, Aug 2025–Jul 2026. Toggle to see the segment or channel split over the period. July 2026 is a part-month (data to 8 Jul).</div>
      <div class="seg" id="seasSeg">
        <button data-m="total" class="on">Total</button>
        <button data-m="segment">By segment</button>
        <button data-m="channel">By channel</button>
      </div>
      <div class="chart-box chart-tall"><canvas id="seasChart"></canvas></div>
    </div>
  </div>

  <div class="grid g3">
    <div class="card">
      <button class="dl" data-dl="top">⬇ PNG</button>
      <h3>Top 20 Spenders</h3>
      <div class="cap">Ranked by total measured spend, Aug 2025–Jul 2026.</div>
      <div class="chart-box" style="height:560px"><canvas id="topChart"></canvas></div>
    </div>
    <div class="card">
      <button class="dl" data-dl="seg">⬇ PNG</button>
      <h3>{seg_title}</h3>
      <div class="cap">Advertisers grouped into {vertical_name} segments (heuristic, by name).</div>
      <div class="chart-box"><canvas id="segChart"></canvas></div>
      <div class="note">{seg_note}</div>
    </div>
  </div>

  <div class="grid">
    <div class="card">
      <h3>Top 25 Advertisers — detail</h3>
      <div class="cap">Total spend, segment, dominant channel and market structure per advertiser.</div>
      <table id="advTable">
        <thead><tr>
          <th>#</th><th>Advertiser</th><th>Segment</th>
          <th class="num">Total spend</th><th>Share</th><th>Top channel</th><th>Structure</th>
        </tr></thead>
        <tbody></tbody>
      </table>
    </div>
  </div>

  <div class="grid">
    <div class="card">
      <button class="dl" id="fullCsv">⬇ CSV</button>
      <h3>All Advertisers</h3>
      <div class="cap" id="fullCap"></div>
      <div class="seg" id="fullSeg"></div>
      <input type="text" id="fullSearch" placeholder="Search by advertiser name…"
        style="width:100%;background:var(--panel2);border:1px solid var(--line);border-radius:8px;
        color:var(--ink);font-family:inherit;font-size:13px;padding:9px 12px;margin-bottom:12px;outline:none;box-sizing:border-box">
      <div style="max-height:640px;overflow:auto;border:1px solid var(--line);border-radius:10px">
        <table id="fullTable">
          <thead><tr>
            <th>#</th><th>Advertiser</th><th>Segment</th>
            <th class="num">12-mo spend</th><th>Top channel</th><th>Structure</th>
          </tr></thead>
          <tbody></tbody>
        </table>
      </div>
      <div class="note" id="fullFootnote"></div>
    </div>
  </div>

  <div class="grid g2">
    <div class="card">
      <h3>Channel Detail</h3>
      <div class="cap">All measured channels, ranked by 12-month spend.</div>
      <table id="chanTable">
        <thead><tr><th>#</th><th>Channel</th><th class="num">Spend</th><th class="num">Share</th></tr></thead>
        <tbody></tbody>
      </table>
    </div>
    <div class="card">
      <h3>Key Insights</h3>
      <div class="cap">What stands out in the Aug 2025–Jul 2026 data.</div>
      <div class="insights" id="insights"></div>
    </div>
  </div>

  <footer id="foot"></footer>
</div>

<script>
const DATA = {data_json};
const PAL = ['#FDB600','#585858','#7A7A7A','#9E9E9E','#C2C2C2','#E0E0E0','#4D4D4D','#8C8C8C','#B3B3B3','#D2D2D2','#6B6B6B','#EDEDED'];
const STRUCT_COLORS = ['#FDB600','#585858','#9E9E9E','#C2C2C2'];
const fmtM = v => '$'+(v/1e6).toFixed(1)+'M';
const fmt$ = v => '$'+Math.round(v).toLocaleString();
const pct  = (v,t)=> (v/t*100).toFixed(1)+'%';
const GT = DATA.grand_total;
Chart.defaults.color = '#585858';
Chart.defaults.font.family = "'Poppins',sans-serif";
Chart.defaults.font.size = 12;
Chart.defaults.font.weight = 300;
const gridc = 'rgba(0,0,0,.08)';

document.getElementById('hero-total').textContent = fmtM(GT);
document.getElementById('tag-scope').textContent =
  DATA.n_advertisers.toLocaleString()+' advertisers · '+DATA.n_channels+' media channels · 12 months';

document.getElementById('kpis').innerHTML = DATA.kpis.map(k=>
  `<div class="kpi"><div class="v" style="font-size:${{k.v.length>10?'18px':'26px'}}">${{k.v}}</div>
   <div class="l">${{k.l}}</div>${{k.d?`<div class="d">${{k.d}}</div>`:''}}</div>`).join('');

const REG = {{}};
function chartToPng(chart, filename){{
  if(!chart) return;
  const src = chart.canvas, scale = 2;
  const tmp = document.createElement('canvas');
  tmp.width = src.width * scale; tmp.height = src.height * scale;
  const ctx = tmp.getContext('2d');
  ctx.fillStyle = '#FFFFFF';
  ctx.fillRect(0,0,tmp.width,tmp.height);
  ctx.drawImage(src,0,0,tmp.width,tmp.height);
  const a = document.createElement('a');
  a.href = tmp.toDataURL('image/png');
  a.download = filename; a.click();
}}
const DLNAMES = {{struct:'market-structure', channel:'channel-mix', seas:'monthly-seasonality',
                 top:'top-20-spenders', seg:'spend-by-segment'}};

const structK = Object.keys(DATA.structure), structV = structK.map(k=>DATA.structure[k]);
REG.struct = new Chart(structChart,{{type:'doughnut',
  data:{{labels:structK,datasets:[{{data:structV,backgroundColor:STRUCT_COLORS,borderColor:'#FFFFFF',borderWidth:3}}]}},
  options:{{cutout:'58%',plugins:{{legend:{{position:'right'}},
    tooltip:{{callbacks:{{label:c=>c.label+': '+fmtM(c.parsed)+' ('+pct(c.parsed,GT)+')'}}}}}}}}}});
document.getElementById('struct-note').textContent = DATA.struct_note;

const chK=Object.keys(DATA.channel), chV=chK.map(k=>DATA.channel[k]);
REG.channel = new Chart(channelChart,{{type:'bar',
  data:{{labels:chK,datasets:[{{data:chV,backgroundColor:PAL,borderRadius:5}}]}},
  options:{{indexAxis:'y',plugins:{{legend:{{display:false}},
    tooltip:{{callbacks:{{label:c=>fmtM(c.parsed.x)+' ('+pct(c.parsed.x,GT)+')'}}}}}},
    scales:{{x:{{grid:{{color:gridc}},ticks:{{callback:v=>'$'+v/1e6+'M'}}}},y:{{grid:{{display:false}}}}}}}}}});

let seasChartObj;
function drawSeas(mode){{
  if(seasChartObj) seasChartObj.destroy();
  let ds, stacked=false, type='line';
  if(mode==='total'){{
    ds=[{{label:'Total spend',data:DATA.month_tot,borderColor:'#FDB600',backgroundColor:'rgba(253,182,0,.14)',
      pointBackgroundColor:'#FDB600',fill:true,tension:.35,borderWidth:2.5,pointRadius:3}}];
  }} else {{
    stacked=true; type='bar';
    const src = mode==='segment'?DATA.segment_month:DATA.channel_month;
    const keys = mode==='segment'?Object.keys(DATA.segment):Object.keys(DATA.channel);
    ds = keys.map((k,i)=>({{label:k,data:src[k],backgroundColor:PAL[i%PAL.length],borderRadius:3}}));
  }}
  seasChartObj=REG.seas=new Chart(seasChart,{{type,
    data:{{labels:DATA.months,datasets:ds}},
    options:{{plugins:{{legend:{{display:mode!=='total',position:'top'}},
      tooltip:{{callbacks:{{label:c=>c.dataset.label+': '+fmtM(c.parsed.y)}}}}}},
      scales:{{x:{{stacked,grid:{{display:false}}}},
        y:{{stacked,grid:{{color:gridc}},ticks:{{callback:v=>'$'+v/1e6+'M'}}}}}}}}}});
}}
drawSeas('total');
document.querySelectorAll('#seasSeg button').forEach(b=>b.onclick=()=>{{
  document.querySelectorAll('#seasSeg button').forEach(x=>x.classList.remove('on'));
  b.classList.add('on'); drawSeas(b.dataset.m);
}});

document.querySelectorAll('.dl').forEach(btn=>btn.addEventListener('click',()=>{{
  const k = btn.dataset.dl;
  if(!DLNAMES[k]) return;
  chartToPng(REG[k], '{slug}-'+DLNAMES[k]+'-aug25-jul26.png');
}}));

const t20=DATA.top_advertisers.slice(0,20);
REG.top = new Chart(topChart,{{type:'bar',
  data:{{labels:t20.map(a=>a.advertiser),datasets:[{{data:t20.map(a=>a.total),
    backgroundColor:t20.map((_,i)=>i<3?'#FDB600':'#585858'),borderRadius:5}}]}},
  options:{{indexAxis:'y',plugins:{{legend:{{display:false}},
    tooltip:{{callbacks:{{label:c=>fmtM(c.parsed.x)+' ('+pct(c.parsed.x,GT)+')'}}}}}},
    scales:{{x:{{grid:{{color:gridc}},ticks:{{callback:v=>'$'+v/1e6+'M'}}}},y:{{grid:{{display:false}},ticks:{{font:{{size:11}}}}}}}}}}}});

const segK=Object.keys(DATA.segment), segV=segK.map(k=>DATA.segment[k]);
REG.seg = new Chart(segChart,{{type:'doughnut',
  data:{{labels:segK,datasets:[{{data:segV,backgroundColor:PAL,borderColor:'#FFFFFF',borderWidth:3}}]}},
  options:{{cutout:'55%',plugins:{{legend:{{position:'right',labels:{{font:{{size:10.5}},boxWidth:12}}}},
    tooltip:{{callbacks:{{label:c=>c.label+': '+fmtM(c.parsed)+' ('+pct(c.parsed,GT)+')'}}}}}}}}}});

const topChanOf = a => Object.entries(a.channels||{{}}).sort((x,y)=>y[1]-x[1])[0];
const maxT=DATA.top_advertisers[0].total;
document.querySelector('#advTable tbody').innerHTML = DATA.top_advertisers.slice(0,25).map((a,i)=>{{
  const tc=topChanOf(a);
  return `<tr><td>${{i+1}}</td><td>${{a.advertiser}}</td><td><span class="pill">${{a.segment}}</span></td>
   <td class="num bar-cell"><div class="bar-fill" style="width:${{a.total/maxT*100}}%"></div><span>${{fmt$(a.total)}}</span></td>
   <td>${{pct(a.total,GT)}}</td>
   <td>${{tc?tc[0]+' ('+pct(tc[1],a.total)+')':'—'}}</td>
   <td><span class="pill">${{a.structure}}</span></td></tr>`;
}}).join('');

document.querySelector('#chanTable tbody').innerHTML = chK.map((c,i)=>
  `<tr><td>${{i+1}}</td><td>${{c}}</td><td class="num">${{fmt$(DATA.channel[c])}}</td><td class="num">${{pct(DATA.channel[c],GT)}}</td></tr>`).join('');

// ALL ADVERTISERS — full list, filterable by segment + free-text search
const FULL = DATA.full_list;
document.getElementById('fullCap').textContent =
  `Every advertiser in the {vertical_name} dataset — ${{FULL.length.toLocaleString()}} in total, ${{fmtM(GT)}} combined. Sorted high to low; filter by segment or search by name.`;
const fullSegs = ['All', ...Array.from(new Set(FULL.map(f=>f.segment))).sort()];
let fullFilter = 'All', fullSearch = '';
document.getElementById('fullSeg').innerHTML = fullSegs.map((c,i)=>
  `<button data-c="${{c}}" class="${{i===0?'on':''}}">${{c}}${{c==='All'?' ('+FULL.length+')':' ('+FULL.filter(f=>f.segment===c).length+')'}}</button>`).join('');
function renderFull(){{
  const term = fullSearch.trim().toLowerCase();
  const rows = FULL.filter(f=>(fullFilter==='All'||f.segment===fullFilter)&&(!term||f.advertiser.toLowerCase().includes(term)));
  const maxV = Math.max(...rows.map(f=>f.total),1);
  document.querySelector('#fullTable tbody').innerHTML = rows.map((f,i)=>
    `<tr><td>${{i+1}}</td><td>${{f.advertiser}}</td><td><span class="pill">${{f.segment}}</span></td>
     <td class="num bar-cell"><div class="bar-fill" style="width:${{f.total/maxV*100}}%"></div><span>${{fmt$(f.total)}}</span></td>
     <td>${{f.top_channel}}${{f.top_channel!=='—'?' ('+(f.top_channel_pct*100).toFixed(0)+'%)':''}}</td>
     <td><span class="pill">${{f.structure}}</span></td></tr>`).join('');
  document.getElementById('fullFootnote').textContent = `Showing ${{rows.length.toLocaleString()}} of ${{FULL.length.toLocaleString()}} advertisers.`;
}}
renderFull();
document.querySelectorAll('#fullSeg button').forEach(b=>b.onclick=()=>{{
  document.querySelectorAll('#fullSeg button').forEach(x=>x.classList.remove('on'));
  b.classList.add('on'); fullFilter=b.dataset.c; renderFull();
}});
document.getElementById('fullSearch').addEventListener('input', e=>{{ fullSearch=e.target.value; renderFull(); }});
document.getElementById('fullCsv').onclick=()=>{{
  const hdr=['Rank','Advertiser','Segment','12-month spend (AUD)','Top channel','Top channel share','Structure'];
  const lines=[hdr.join(',')].concat(FULL.map((f,i)=>
    [i+1,'"'+f.advertiser.replace(/"/g,'""')+'"',f.segment,Math.round(f.total),
     f.top_channel,(f.top_channel_pct*100).toFixed(1)+'%',f.structure].join(',')));
  const blob=new Blob([lines.join('\n')],{{type:'text/csv'}});
  const a=document.createElement('a');a.href=URL.createObjectURL(blob);
  a.download='{slug}-all-advertisers-aug25-jul26.csv';a.click();
}};

document.getElementById('insights').innerHTML = DATA.insights.map(x=>
  `<div class="ins"><div class="h">${{x.h}}</div><p>${{x.p}}</p></div>`).join('');

document.getElementById('foot').innerHTML =
  `<div style="font-weight:600;color:#0A0A0A;text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px">Sunny Advertising<span style="color:#FDB600">.</span> &nbsp;·&nbsp; Your Media Performance Partners</div>`+
  `Source: {vertical_name} Media Spends, Aug 2025–Jul 2026 (Nielsen Ad Intel categorisation). Figures are estimated measured media spend at rate card, excluding creative/production. `+
  `Channel classification derived from media-type naming. Segment and market-structure grouping is heuristic (by advertiser name) and may misclassify diversified or unfamiliar brands. July 2026 reflects data to 8 July only.`;
</script>
</body>
</html>
"""

def render(vertical, DATA):
    html = TEMPLATE.format(
        page_title=vertical['page_title'],
        h1=vertical['h1'],
        struct_title=vertical['struct_title'],
        struct_cap=vertical['struct_cap'],
        seg_title=vertical['seg_title'],
        seg_note=vertical['seg_note'],
        vertical_name=vertical['name'],
        slug=vertical['slug'],
        data_json=json.dumps(DATA),
    )
    out_path = f"{OUT_DIR}/{vertical['slug']}-media-spend-aug25-jul26.html"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print("wrote", out_path, fmtM(DATA['grand_total']), DATA['n_advertisers'], "advertisers")
    return out_path
