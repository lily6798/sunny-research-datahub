#!/usr/bin/env python3
"""Rebuild dashboards/travel-tourism-media-spend-2025.html straight from the raw Nielsen
Ad Intel export. Travel & Tourism has its own script (not the shared generator/verticals.py
pipeline) because its schema differs: the raw file has a Media Network dimension instead of
a coarse Media Type column, and its "geo" lens is a per-advertiser Metro/Regional/National
spend breakdown rather than a single name-derived label like the other verticals' "structure".

Run: cd generator && python3 travel_rebuild.py   (needs pandas + openpyxl)
"""
import json
import re
import os
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
NIELSEN_FILE = os.path.join(HERE, "..", "data", "nielsen", "Travel and Tourism.xlsx")
OUT_PATH = os.path.join(HERE, "..", "dashboards", "travel-tourism-media-spend-2025.html")
KNOWN_PATH = os.path.join(HERE, "travel_known.json")
MONTH_LABELS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

def fmtM(v): return f"${v/1e6:.1f}M"
def fmt_dollar(v): return f"${round(v):,}"
def pct(v, t): return f"{v/t*100:.1f}%" if t else "0.0%"

# ============================================================ NETWORK -> CHANNEL (verified against
# original published channel totals: OOH/Radio/Cinema/Other match exactly; Newspapers/Digital/TV/Magazines
# are close but not bit-exact since the original mapping key isn't available — 3 genuinely ambiguous
# networks (Switzer, True North Media Australia, Pt 78) go to Other/Unclassified rather than being guessed.
NETWORK_CHANNEL = {
    'News Corp Australia Newspapers':'Newspapers','Nine Publishing':'Newspapers',
    'Australian Community Media':'Newspapers','West Aust Newspapers':'Newspapers',
    'News Corp Australia NIMs':'Newspapers','News Australia':'Newspapers',
    'Nine Publishing NIMs':'Newspapers','SA Today':'Newspapers','Independant Newspapers':'Newspapers',
    'OUTDOOR':'Out of Home',
    'YouTube':'Digital & Social','Instagram':'Digital & Social','Facebook':'Digital & Social',
    'Other Digital Networks':'Digital & Social','Nine Digital':'Digital & Social','TikTok':'Digital & Social',
    'Pinterest':'Digital & Social','LinkedIn':'Digital & Social','Yahoo':'Digital & Social',
    'X':'Digital & Social','Are Media Digital':'Digital & Social','ACM Digital':'Digital & Social',
    'NET9':'Television','NET7':'Television','10':'Television','7 Regional':'Television',
    '9 Regional':'Television','SBS':'Television','10 Regional':'Television','NBN':'Television',
    '7TWO':'Television','7Mate':'Television','9Life':'Television','GO':'Television',
    '10 Drama':'Television','GEM':'Television','7Two Regional':'Television','9Life Regional':'Television',
    '7Flix Regional':'Television','SBS Regional':'Television','7Mate Regional':'Television',
    '7Bravo Regional':'Television','9Rush':'Television','10 Comedy':'Television',
    'GEM Regional':'Television','7FLIX':'Television','NBN 9Life':'Television','GO Regional':'Television',
    'SBS VICELAND':'Television','SBS Food':'Television','7Bravo':'Television',
    '10 Comedy Regional':'Television','10 Drama Regional':'Television','NBN GEM':'Television',
    'NTD':'Television','SBS World Movies':'Television','SBS Food Regional':'Television',
    'NBN GO':'Television','SBS VICELAND Regional':'Television','Nickelodeon':'Television',
    'SKY News Regional':'Television','SBS World Movies Regional':'Television',
    'Nickelodeon Regional':'Television','GO DAR':'Television','9Life DAR':'Television',
    'GEM DAR':'Television','Racing.com':'Television',
    'Nova Entertainment':'Radio','ARN Radio':'Radio','Southern Cross Austereo':'Radio',
    'Nine Radio':'Radio','Grant Broadcasters':'Radio','ARN':'Radio','Broadcast Operations Group':'Radio',
    'Cinema':'Cinema',
    'News Corp Australia Custom Magazines':'Magazines','Australian Traveller':'Magazines',
    'Are Media':'Magazines','Other Mags':'Magazines','West Australian Magazines':'Magazines',
    'News Corp Australia Magazines':'Magazines','Indesign Media Asia Pacific':'Magazines',
    'Readers Digest':'Magazines','Time Inc':'Magazines','Success Publishing':'Magazines',
    'KK Press':'Magazines','Daily Mail & General Trust':'Magazines','Hardie Grant Media':'Magazines',
    'RM Williams Outback':'Magazines','The Monthly':'Magazines','Universal Magazines':'Magazines',
    'Next Media':'Magazines',
    'Alternative Technology Association':'Other / Unclassified','User':'Other / Unclassified',
    'Created':'Other / Unclassified','The Nielsen Company © 2026':'Other / Unclassified',
    'Switzer':'Other / Unclassified','True North Media Australia':'Other / Unclassified','Pt 78':'Other / Unclassified',
}

REGIONAL_NETWORKS = {'Australian Community Media','NBN','NBN 9Life','NBN GEM','NBN GO','Grant Broadcasters'}
NATIONAL_CHANNELS = {'Digital & Social', 'Out of Home', 'Cinema'}

def network_geo(network, channel):
    if 'Regional' in network or network in REGIONAL_NETWORKS:
        return 'Regional'
    if channel in NATIONAL_CHANNELS:
        return 'National'
    return 'Metro'

def channel_for(network):
    return NETWORK_CHANNEL.get(network, 'Other / Unclassified')

# ============================================================ ADVERTISER -> CATEGORY
with open(KNOWN_PATH) as f:
    KNOWN = json.load(f)

AIRLINE_KW = ['airlines','airways','air new zealand','jetstar','qantas','virgin australia','scoot',
    'airasia','air asia','cathay pacific','malaysia airlines','singapore airlines','emirates',
    'qatar airways','fiji airways','philippine airlines','china southern','china eastern','etihad',
    'garuda indonesia','japan airlines','all nippon','korean air','thai airways','vietnam airlines']
CRUISE_KW = ['cruise','cruises','cunard','carnival cruise','celebrity cruises','princess cruise',
    'royal caribbean','norwegian cruise','holland america','msc cruises','p&o cruises','oceania cruises',
    'silversea','viking river','viking cruises','ponant','scenic luxury cruises']
OTA_KW = ['booking.com','expedia','airbnb','stayz','trivago','webjet','wotif','kayak','tripadeal',
    'luxury escapes','ignite travel','agoda','hotels.com','hopper','skyscanner','despegar']
TOURISM_BOARD_KW = ['tourism board','tourism australia','tourism new zealand','tourist commission',
    'tourism commission','destination nsw','visit victoria','tourism tasmania','tourism & events',
    'tourism tropical','sa tourism','nt tourist','destination gold coast','experience gold coast',
    'destination southern','visit ']
HOTEL_KW = ['hotel','resort','marriott','shangri-la','intercontinental','accor','hilton','hyatt',
    'ibis hotel','holiday inn','walt disney parks','wyndham','best western','crown resorts','mantra']
TOUR_OPERATOR_KW = ['tours','travel agency','holidays of','vacations','flight centre','helloworld',
    'contiki','trafalgar','insight vacations','globus','wendy wu','captains choice','bunnik',
    'intrepid','journey beyond','scenic tours','house of travel','phil hoffman','spacifica travel',
    'geelong travel','top deck','discovery holiday parks','big4 holiday parks','asia vacation',
    'travel co','travel group','travelrite',' travel',' tour ']

def category_for(name):
    n = name.lower()
    if n in KNOWN: return KNOWN[n]
    if any(k in n for k in AIRLINE_KW): return "Airlines"
    if any(k in n for k in CRUISE_KW): return "Cruise Lines"
    if any(k in n for k in OTA_KW): return "OTA / Booking Platform"
    if any(k in n for k in TOURISM_BOARD_KW): return "Tourism Board / Destination"
    if any(k in n for k in HOTEL_KW): return "Hotels / Resorts"
    if any(k in n for k in TOUR_OPERATOR_KW): return "Tour Operator / Agency"
    return "Other"

def geo_lean_label(geo):
    m, r, n = geo.get('Metro',0), geo.get('Regional',0), geo.get('National',0)
    if n >= m + r: return 'National/Digital'
    if r > m*0.9: return 'Regional-strong'
    if m > 0 and r/(m+r) > 0.2: return 'Metro + some regional'
    return 'Metro'

def build():
    df = pd.read_excel(NIELSEN_FILE, header=None, skiprows=7)
    df.columns = ['advertiser','media_network','total'] + [f'm{i}' for i in range(1,13)]
    df = df[df['advertiser'].notna()]
    df = df[df['advertiser'] != 'Grand Total'].copy()
    for c in ['total'] + [f'm{i}' for i in range(1,13)]:
        df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)

    adv_rows = df[df['media_network'].isna()].copy()
    net_rows = df[df['media_network'].notna()].copy()
    net_rows['channel'] = net_rows['media_network'].map(channel_for)
    net_rows['geo'] = net_rows.apply(lambda r: network_geo(r['media_network'], r['channel']), axis=1)

    grand_total = float(adv_rows['total'].sum())
    n_advertisers = int((adv_rows['total'] > 0).sum())
    n_networks = net_rows['media_network'].nunique()

    month_tot = [float(adv_rows[f'm{i+1}'].sum()) for i in range(12)]

    channel_tot = net_rows.groupby('channel')['total'].sum().sort_values(ascending=False)
    channel = {k: float(v) for k, v in channel_tot.items()}
    channel_month = {ch: [float(net_rows[net_rows['channel']==ch][f'm{i+1}'].sum()) for i in range(12)] for ch in channel}

    geo_tot = net_rows.groupby('geo')['total'].sum()
    geo = {k: float(geo_tot.get(k, 0)) for k in ['Metro','National','Regional']}
    geo_month = {g: [float(net_rows[net_rows['geo']==g][f'm{i+1}'].sum()) for i in range(12)] for g in geo}

    top_net_tot = net_rows.groupby('media_network').agg(total=('total','sum'), channel=('channel','first'), geo=('geo','first')).sort_values('total', ascending=False)
    top_networks = [{"network": idx, "channel": r['channel'], "geo": r['geo'], "total": float(r['total'])}
                     for idx, r in top_net_tot.head(25).iterrows()]

    adv_names = adv_rows[adv_rows['total'] > 0].sort_values('total', ascending=False).copy()
    adv_names['category'] = adv_names['advertiser'].map(category_for)

    category_tot = adv_names.groupby('category')['total'].sum().sort_values(ascending=False)
    category = {k: float(v) for k, v in category_tot.items()}
    category_month = {c: [float(adv_names[adv_names['category']==c][f'm{i+1}'].sum()) for i in range(12)] for c in category}

    def channels_and_geo_for(name):
        sub = net_rows[net_rows['advertiser'] == name]
        ch_out, geo_out = {}, {'Metro':0.0,'Regional':0.0,'National':0.0}
        for _, r in sub.iterrows():
            if r['total'] > 0:
                ch_out[r['channel']] = ch_out.get(r['channel'], 0) + float(r['total'])
                geo_out[r['geo']] = geo_out.get(r['geo'], 0) + float(r['total'])
        ch_out = {k: v for k, v in ch_out.items() if v > 0}
        geo_out = {k: v for k, v in geo_out.items() if v > 0}
        return ch_out, geo_out

    top_advertisers = []
    for _, r in adv_names.head(70).iterrows():
        ch_out, geo_out = channels_and_geo_for(r['advertiser'])
        top_advertisers.append({
            "advertiser": r['advertiser'], "total": float(r['total']), "category": r['category'],
            "monthly": [float(r[f'm{i+1}']) for i in range(12)],
            "channels": ch_out, "geo": geo_out,
        })

    # category_channel cross-tab (for parity with original, not currently charted but kept for completeness)
    category_channel = {}
    for cat in category:
        sub = adv_names[adv_names['category']==cat]['advertiser']
        cc = net_rows[net_rows['advertiser'].isin(sub)].groupby('channel')['total'].sum()
        category_channel[cat] = {k: float(v) for k, v in cc.items() if v > 0}

    # full advertiser list (every advertiser, not just top 70) — dominant channel + geo lean label
    chan_pivot = net_rows.groupby(['advertiser','channel'])['total'].sum().reset_index().sort_values('total', ascending=False)
    top_chan_lookup = chan_pivot.drop_duplicates('advertiser').set_index('advertiser')

    full_list = []
    for _, r in adv_names.iterrows():
        name = r['advertiser']
        tc = top_chan_lookup.loc[name] if name in top_chan_lookup.index else None
        _, geo_out = channels_and_geo_for(name)
        full_list.append({
            "advertiser": name, "total": float(r['total']), "segment": r['category'],
            "structure": geo_lean_label(geo_out),
            "top_channel": tc['channel'] if tc is not None else "—",
            "top_channel_pct": round(float(tc['total'])/r['total'], 4) if tc is not None and r['total'] else 0,
        })

    return dict(
        grand_total=grand_total, n_advertisers=n_advertisers, n_networks=n_networks,
        months=MONTH_LABELS, month_tot=month_tot, channel=channel, channel_month=channel_month,
        geo=geo, geo_month=geo_month, top_networks=top_networks, top_advertisers=top_advertisers,
        category=category, category_month=category_month, category_channel=category_channel,
        full_list=full_list,
    )

def splice_into_html(DATA):
    """Swap the DATA blob and the mid-tier band section for a full-advertiser-list section
    in the existing dashboard HTML, leaving the rest of the file (CSS, charts, insights,
    top-networks table, footer) untouched."""
    html = open(OUT_PATH).read()

    new_data_line = "const DATA = " + json.dumps(DATA) + ";"
    html, n = re.subn(r"const DATA = \{.*?\};\n// Sunny-branded",
                       lambda m: new_data_line + "\n// Sunny-branded", html, flags=re.S)
    assert n == 1, f"DATA replace count={n}, expected 1"

    old_band_html = '''  <!-- Mid-tier band $500k-$3M -->
  <div class="grid">
    <div class="card">
      <button class="dl" id="bandCsv">⬇ CSV</button>
      <h3>Mid-Tier Advertisers — spending $1M to $8M in 2025</h3>
      <div class="cap" id="bandCap"></div>
      <div class="seg" id="bandSeg"></div>
      <div style="max-height:560px;overflow:auto;border:1px solid var(--line);border-radius:10px">
        <table id="bandTable">
          <thead><tr>
            <th>#</th><th>Advertiser</th><th>Category</th>
            <th class="num">Annual spend</th><th>Top channel</th><th>Geo lean</th>
          </tr></thead>
          <tbody></tbody>
        </table>
      </div>
      <div class="note">The "mid-market" of travel advertising — established brands and challengers running sustained campaigns below the mega-spenders. 79 advertisers, $218.5M combined.</div>
    </div>
  </div>'''

    new_full_html = '''  <!-- All Advertisers -->
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
            <th>#</th><th>Advertiser</th><th>Category</th>
            <th class="num">Annual spend</th><th>Top channel</th><th>Geo lean</th>
          </tr></thead>
          <tbody></tbody>
        </table>
      </div>
      <div class="note" id="fullFootnote"></div>
    </div>
  </div>'''

    if old_band_html in html:
        html = html.replace(old_band_html, new_full_html)
    else:
        assert '<h3>All Advertisers</h3>' in html, "neither old band nor new full-list HTML found — file structure changed unexpectedly"

    old_band_js_start = "// MID-TIER BAND $500k-$3M"
    new_js_start = "// ALL ADVERTISERS — full list, filterable by category + free-text search"
    end_marker = "// INSIGHTS"

    new_full_js = '''// ALL ADVERTISERS — full list, filterable by category + free-text search
const FULL = DATA.full_list;
document.getElementById('fullCap').textContent =
  `Every advertiser in the Travel & Tourism dataset — ${FULL.length.toLocaleString()} in total, ${fmtM(GT)} combined. Sorted high to low; filter by category or search by name.`;
const fullCats = ['All', ...Array.from(new Set(FULL.map(f=>f.segment))).sort()];
let fullFilter = 'All', fullSearch = '';
document.getElementById('fullSeg').innerHTML = fullCats.map((c,i)=>
  `<button data-c="${c}" class="${i===0?'on':''}">${c}${c==='All'?' ('+FULL.length+')':' ('+FULL.filter(f=>f.segment===c).length+')'}</button>`).join('');
function renderFull(){
  const term = fullSearch.trim().toLowerCase();
  const rows = FULL.filter(f=>(fullFilter==='All'||f.segment===fullFilter)&&(!term||f.advertiser.toLowerCase().includes(term)));
  const maxV = Math.max(...rows.map(f=>f.total),1);
  document.querySelector('#fullTable tbody').innerHTML = rows.map((f,i)=>
    `<tr><td>${i+1}</td><td>${f.advertiser}</td><td><span class="pill">${f.segment}</span></td>
     <td class="num bar-cell"><div class="bar-fill" style="width:${f.total/maxV*100}%"></div><span>${fmt$(f.total)}</span></td>
     <td>${f.top_channel}${f.top_channel!=='—'?' ('+(f.top_channel_pct*100).toFixed(0)+'%)':''}</td>
     <td><span class="pill">${f.structure}</span></td></tr>`).join('');
  document.getElementById('fullFootnote').textContent = `Showing ${rows.length.toLocaleString()} of ${FULL.length.toLocaleString()} advertisers.`;
}
renderFull();
document.querySelectorAll('#fullSeg button').forEach(b=>b.onclick=()=>{
  document.querySelectorAll('#fullSeg button').forEach(x=>x.classList.remove('on'));
  b.classList.add('on'); fullFilter=b.dataset.c; renderFull();
});
document.getElementById('fullSearch').addEventListener('input', e=>{ fullSearch=e.target.value; renderFull(); });
document.getElementById('fullCsv').onclick=()=>{
  const hdr=['Rank','Advertiser','Category','Annual spend (AUD)','Top channel','Top channel share','Geo lean'];
  const lines=[hdr.join(',')].concat(FULL.map((f,i)=>
    [i+1,'"'+f.advertiser.replace(/"/g,'""')+'"',f.segment,Math.round(f.total),
     f.top_channel,(f.top_channel_pct*100).toFixed(1)+'%',f.structure].join(',')));
  const blob=new Blob([lines.join('\\n')],{type:'text/csv'});
  const a=document.createElement('a');a.href=URL.createObjectURL(blob);
  a.download='travel-tourism-all-advertisers-2025.csv';a.click();
};

'''

    if old_band_js_start in html:
        start_i = html.index(old_band_js_start)
        end_i = html.index(end_marker)
        html = html[:start_i] + new_full_js + html[end_i:]
    elif new_js_start in html:
        start_i = html.index(new_js_start)
        end_i = html.index(end_marker)
        html = html[:start_i] + new_full_js + html[end_i:]
    else:
        raise AssertionError("neither old nor new JS block found — file structure changed unexpectedly")

    with open(OUT_PATH, "w") as f:
        f.write(html)


if __name__ == "__main__":
    DATA = build()
    print("grand_total:", fmtM(DATA['grand_total']))
    print("n_advertisers:", DATA['n_advertisers'])
    print("n_networks:", DATA['n_networks'])
    print("channel:", {k: fmtM(v) for k, v in DATA['channel'].items()})
    print("geo:", {k: fmtM(v) for k, v in DATA['geo'].items()})
    print("category:", {k: fmtM(v) for k, v in DATA['category'].items()})
    splice_into_html(DATA)
    print("Wrote", OUT_PATH)
