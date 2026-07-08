import re
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_dashboards import build, render, fmtM, pct

def lc(s): return str(s).lower()

# ============================================================ MOTOR VEHICLES
MV_CHINESE = ['byd','great wall','gwm','haval','saic','mg motor',' mg ','chery','geely','ldv',
              'jac motors','baic','changan','omoda','deepal','zeekr','foton','maxus']
MV_KOREAN  = ['kia motors','hyundai','genesis motors']
MV_JAPANESE= ['toyota','mazda','mitsubishi','nissan','isuzu','subaru','honda','lexus','suzuki','daihatsu']
MV_EUROPEAN= ['volkswagen','volvo','bmw','land rover','jaguar','audi','mercedes','renault','peugeot',
              'citroen','seat motor','polestar','skoda','fiat','alfa romeo','porsche','mini ','ferrari',
              'lamborghini','maserati','bentley','rolls royce','aston martin']
MV_AMERICAN= ['ford motor','general motors','chevrolet','jeep','ram trucks','chrysler','cadillac','gmc','tesla']
MV_DEALER  = ['dealer','motor group','cox automotive']
MV_AFTERM  = ['tyre','tire','t-mart','motoring & services','bridgestone','mycar','tyrepower','goodyear',
              'continental tyres','pirelli']
MV_MARKET  = ['carsales','drive.com','gumtree','autotrader','redbook','nine digital','carsguide']

def mv_category(name):
    n = lc(name)
    if any(k in n for k in MV_DEALER): return "Dealer Networks"
    if any(k in n for k in MV_AFTERM): return "Aftermarket & Services"
    if any(k in n for k in MV_MARKET): return "Marketplace & Digital"
    if any(k in n for k in MV_CHINESE): return "Chinese OEM"
    if any(k in n for k in MV_KOREAN): return "Korean OEM"
    if any(k in n for k in MV_JAPANESE): return "Japanese OEM"
    if any(k in n for k in MV_EUROPEAN): return "European OEM"
    if any(k in n for k in MV_AMERICAN): return "American OEM"
    return "Other OEM & Specialty"

def mv_structure(name):
    cat = mv_category(name)
    if cat == "Chinese OEM": return "Chinese Challenger Brands"
    if cat in ("Dealer Networks","Aftermarket & Services"): return "Dealer Networks & Aftermarket"
    if cat == "Marketplace & Digital": return "Marketplace & Digital"
    return "Legacy & Established OEMs"

def mv_struct_note(structure, gt, fmtM, pct):
    chinese = structure.get("Chinese Challenger Brands", 0)
    legacy = structure.get("Legacy & Established OEMs", 0)
    return (f"Chinese challenger brands (BYD, Great Wall, SAIC, Chery, Geely, LDV) have built to "
            f"{fmtM(chinese)} ({pct(chinese,gt)}) of measured spend vs {fmtM(legacy)} ({pct(legacy,gt)}) "
            f"from legacy & established OEMs — a rapid, well-funded market entry.")

def mv_insights(d):
    ch = d['channel']; seg = d['segment']; struct = d['structure']; t0 = d['t0']
    fmtM_, pct_ = d['fmtM'], d['pct']
    gt = d['grand_total']
    chinese = struct.get("Chinese Challenger Brands", 0)
    tv = ch.get('Television', 0); disp = ch.get('Digital Display', 0)
    chinese_brands_n = sum(1 for a in d['top_advertisers'] if mv_category(a['advertiser'])=="Chinese OEM")
    return [
        {"h":"Television still leads Motor Vehicles","p":f"Television takes <b>{fmtM_(tv)}</b> ({pct_(tv,gt)}) of spend — the biggest single channel — with Digital Display close behind at {fmtM_(disp)} ({pct_(disp,gt)}), reflecting big-budget brand campaigns from major OEMs."},
        {"h":"A defined seasonal dip","p":f"Spend peaks in <b>{d['months'][d['pk_i']]}</b> ({fmtM_(d['month_tot'][d['pk_i']])}) and bottoms out in <b>{d['months'][d['tr_i']]}</b> ({fmtM_(d['month_tot'][d['tr_i']])}) — a ~{d['swing_pct']}% swing across the 12 months (excl. the partial July read)."},
        {"h":"Chinese brands are buying share aggressively","p":f"Chinese challenger OEMs account for <b>{pct_(chinese,gt)}</b> of category spend ({fmtM_(chinese)}) among the top spenders alone — a structural shift in how the market is contested."},
        {"h":"A long, fragmented tail","p":f"The top 10 advertisers hold <b>{pct_(d['top10_sum'],gt)}</b> of spend, but {d['n_advertisers']:,} advertisers compete overall — dealer groups, tyre chains and marketplaces fill out a very long tail below the OEMs."},
        {"h":f"{t0['advertiser']} leads the category","p":f"{t0['advertiser']} is the single largest spender at {fmtM_(t0['total'])} ({pct_(t0['total'],gt)}), reflecting the scale of national OEM marketing budgets."},
        {"h":"Out of Home plays a real role","p":f"Motor Vehicles puts <b>{fmtM_(ch.get('Out of Home',0))}</b> ({pct_(ch.get('Out of Home',0),gt)}) into OOH — dealership and launch campaigns lean on high-visibility placements alongside broadcast."},
    ]

MOTOR_VEHICLES = dict(
    file="Motor Vehicles.xlsx", slug="motor-vehicles", name="Motor Vehicles",
    page_title="Motor Vehicles Media Spend — Australia Aug 2025–Jul 2026",
    h1="Motor Vehicles — Australian Media Spend",
    struct_title="Legacy OEM vs Chinese Challenger", struct_kpi_label="Chinese challenger brand share",
    struct_kpi_key="Chinese Challenger Brands",
    struct_cap="Market structure lens — legacy/established OEMs vs Chinese challenger brands vs dealer networks &amp; aftermarket vs marketplace/digital.",
    seg_title="Spend by Motor Vehicles Segment", seg_note="Japanese and European legacy OEMs still dominate overall spend, but Chinese challenger brands are now a top-tier bloc in their own right.",
    structure_fn=mv_structure, category_fn=mv_category, struct_note_fn=mv_struct_note, insights_fn=mv_insights,
)

# ============================================================ AGRICULTURE & FARMING
AG_EXPLICIT = {
    "cnh industrial capital australia":"Machinery & Equipment","pfg australia":"Machinery & Equipment",
    "mahindra australia":"Machinery & Equipment","gentech seeds":"Seed & Genetics",
    "kubota tractors":"Machinery & Equipment","john deere":"Machinery & Equipment",
    "agco australia":"Machinery & Equipment","incitec pivot":"Crop Chemicals & Fertiliser",
    "basf australia":"Crop Chemicals & Fertiliser","advantage feeders":"Livestock Equipment & Genetics",
    "boyd metal works":"Machinery & Equipment","hutton & northey sales":"Farm Services & Retail",
    "shearwell australia":"Livestock Equipment & Genetics","bourgault aust":"Machinery & Equipment",
    "vic chemicals":"Crop Chemicals & Fertiliser","stockpro":"Livestock Equipment & Genetics",
    "boss engineering":"Machinery & Equipment","syngenta australia":"Crop Chemicals & Fertiliser",
    "growers services":"Farm Services & Retail","ausplow":"Machinery & Equipment",
    "sprayline":"Machinery & Equipment","fmc australasia":"Crop Chemicals & Fertiliser",
    "te pari products":"Livestock Equipment & Genetics","afgri equipment australia":"Machinery & Equipment",
    "polaris industries":"Machinery & Equipment","olympus loaders":"Machinery & Equipment",
    "wesfarmers csbp":"Crop Chemicals & Fertiliser","duraquip":"Machinery & Equipment",
    "bayer cropscience":"Crop Chemicals & Fertiliser","grainline":"Seed & Genetics",
    "pacific seeds":"Seed & Genetics","intergrain":"Seed & Genetics","seed terminator":"Machinery & Equipment",
    "central wheatbelt imports":"Farm Services & Retail","nufarm":"Crop Chemicals & Fertiliser",
    "bromar engineering":"Machinery & Equipment","dlf seeds":"Seed & Genetics",
    "ramsey bros":"Machinery & Equipment","th & ee tunley":"Farm Services & Retail",
}
def ag_category(name):
    n = lc(name)
    if n in AG_EXPLICIT: return AG_EXPLICIT[n]
    if 'seed' in n: return "Seed & Genetics"
    if any(k in n for k in ['chemical','crop','fertil','agro','agchem']): return "Crop Chemicals & Fertiliser"
    if any(k in n for k in ['tractor','machinery','equipment','engineering','loader','metal works','implement']): return "Machinery & Equipment"
    if any(k in n for k in ['livestock','stock','feeder','cattle','sheep']): return "Livestock Equipment & Genetics"
    if any(k in n for k in ['services','imports','sales','merchants']): return "Farm Services & Retail"
    return "Other Agribusiness"

def ag_structure(name):
    cat = ag_category(name)
    if cat == "Machinery & Equipment": return "Machinery & Equipment"
    if cat in ("Crop Chemicals & Fertiliser","Seed & Genetics"): return "Crop Inputs (Chemicals & Seed)"
    return "Livestock, Services & Other"

def ag_struct_note(structure, gt, fmtM, pct):
    mach = structure.get("Machinery & Equipment", 0)
    crop = structure.get("Crop Inputs (Chemicals & Seed)", 0)
    return (f"Machinery & equipment brands lead the category at {fmtM(mach)} ({pct(mach,gt)}), with crop "
            f"chemicals, fertiliser and seed genetics a close second at {fmtM(crop)} ({pct(crop,gt)}) — "
            f"capital equipment and input suppliers both advertise hard for the same buyer.")

def ag_insights(d):
    ch = d['channel']; struct = d['structure']; t0 = d['t0']
    fmtM_, pct_ = d['fmtM'], d['pct']; gt = d['grand_total']
    press = ch.get('Press', 0); tv = ch.get('Television', 0)
    return [
        {"h":"Regional media, not metro, carries this category","p":f"Press takes <b>{fmtM_(press)}</b> ({pct_(press,gt)}) of spend and Television {fmtM_(tv)} ({pct_(tv,gt)}) — Agriculture & Farming buys where its audience actually is: regional press and regional TV, not capital-city metro media."},
        {"h":"A defined seasonal pattern","p":f"Spend peaks in <b>{d['months'][d['pk_i']]}</b> ({fmtM_(d['month_tot'][d['pk_i']])}) and bottoms out in <b>{d['months'][d['tr_i']]}</b> ({fmtM_(d['month_tot'][d['tr_i']])}) — a ~{d['swing_pct']}% swing that likely tracks the farming calendar."},
        {"h":"Machinery dollars lead the category","p":f"Machinery & equipment advertisers account for <b>{pct_(struct.get('Machinery & Equipment',0),gt)}</b> of spend — capital-intensive purchases justify sustained media investment."},
        {"h":"A genuinely fragmented market","p":f"The top 10 advertisers hold <b>{pct_(d['top10_sum'],gt)}</b> of spend across {d['n_advertisers']:,} advertisers — Agriculture & Farming is Sunny's smallest measured category by total spend, and highly fragmented even at the top."},
        {"h":f"{t0['advertiser']} is the clear #1","p":f"{t0['advertiser']} leads the category at {fmtM_(t0['total'])} ({pct_(t0['total'],gt)}) — well ahead of the next-largest spender."},
        {"h":"Digital is still a minority channel here","p":f"Social and Digital Display combined take only <b>{pct_(ch.get('Social',0)+ch.get('Digital Display',0),gt)}</b> of spend — agribusiness marketing still leans on traditional regional media over always-on digital."},
    ]

AGRICULTURE = dict(
    file="Agriculture & Farming.xlsx", slug="agriculture-farming", name="Agriculture & Farming",
    page_title="Agriculture & Farming Media Spend — Australia Aug 2025–Jul 2026",
    h1="Agriculture &amp; Farming — Australian Media Spend",
    struct_title="Machinery vs Crop Inputs vs Services", struct_kpi_label="Machinery & equipment share",
    struct_kpi_key="Machinery & Equipment",
    struct_cap="Market structure lens — machinery &amp; equipment vs crop inputs (chemicals &amp; seed) vs livestock, services &amp; other.",
    seg_title="Spend by Agribusiness Segment", seg_note="Machinery, crop chemicals and seed genetics dominate; livestock equipment and farm services make up the long tail.",
    structure_fn=ag_structure, category_fn=ag_category, struct_note_fn=ag_struct_note, insights_fn=ag_insights,
)

# ============================================================ HOSPITALITY FOOD & BEVERAGE
HF_EXPLICIT = {
    "dan murphys":"Liquor Retail Chains","bws-beer wine spirits":"Liquor Retail Chains",
    "wine people":"Wine Specialists","uber":"Delivery Platforms","liquorland":"Liquor Retail Chains",
    "independent brands australia":"Independent Bottle Shops","independent liquor group":"Independent Bottle Shops",
    "united thirsty camel bottleshops":"Independent Bottle Shops","liquor marketing group":"Independent Bottle Shops",
    "paramount liquor":"Independent Bottle Shops","el jannah":"QSR & Casual Dining","sushi hub":"QSR & Casual Dining",
    "wine cru":"Wine Specialists","good pair days":"Wine Specialists","clubs nsw":"Clubs & Licensed Venues",
    "nene chicken":"QSR & Casual Dining","liquor barons":"Independent Bottle Shops",
    "rsl clubs of qld":"Clubs & Licensed Venues","mounties group":"Clubs & Licensed Venues",
    "gillen club":"Clubs & Licensed Venues","fasta pasta restaurants":"QSR & Casual Dining",
    "rsl club greenbank":"Clubs & Licensed Venues","bob's bulk booze":"Independent Bottle Shops",
    "cabra-vale diggers":"Clubs & Licensed Venues","zeus street greek":"QSR & Casual Dining",
    "commercial club albury":"Clubs & Licensed Venues","fassina liquor merchants":"Independent Bottle Shops",
    "roll'd australia":"QSR & Casual Dining","parafield airport liquor store":"Independent Bottle Shops",
    "hog's breath cafe":"QSR & Casual Dining",
}
def hf_category(name):
    n = lc(name)
    if n in HF_EXPLICIT: return HF_EXPLICIT[n]
    if 'wine' in n and 'liquor' not in n: return "Wine Specialists"
    if any(k in n for k in ['liquor','bottleshop','bottle shop','cellar','booze']): return "Independent Bottle Shops"
    if any(k in n for k in ['club','rsl','diggers']): return "Clubs & Licensed Venues"
    if any(k in n for k in ['uber','doordash','menulog','deliveroo']): return "Delivery Platforms"
    if any(k in n for k in ['chicken','pizza','kebab','burger','fried','fasta','sushi','greek',"roll'd",'cafe','restaurant','kitchen','grill','noodle','thai','indian']): return "QSR & Casual Dining"
    return "Restaurants, Bars & Other"

def hf_structure(name):
    cat = hf_category(name)
    if cat in ("Liquor Retail Chains","Independent Bottle Shops","Wine Specialists"): return "Liquor & Beverage Retail"
    if cat == "QSR & Casual Dining": return "QSR & Casual Dining"
    if cat == "Clubs & Licensed Venues": return "Clubs & Licensed Venues"
    return "Delivery Platforms & Other"

def hf_struct_note(structure, gt, fmtM, pct):
    liquor = structure.get("Liquor & Beverage Retail", 0)
    qsr = structure.get("QSR & Casual Dining", 0)
    return (f"Liquor &amp; beverage retail dominates at {fmtM(liquor)} ({pct(liquor,gt)}) of category spend — "
            f"more than triple QSR &amp; casual dining's {fmtM(qsr)} ({pct(qsr,gt)}).")

def hf_insights(d):
    ch = d['channel']; struct = d['structure']; t0 = d['t0']
    fmtM_, pct_ = d['fmtM'], d['pct']; gt = d['grand_total']
    soc = ch.get('Social',0); press = ch.get('Press',0)
    return [
        {"h":"Liquor retail sets the pace","p":f"Liquor &amp; beverage retail chains and independent bottle shops together drive <b>{pct_(struct.get('Liquor & Beverage Retail',0),gt)}</b> of category spend — this is fundamentally a liquor-retail-led category, not a restaurant one."},
        {"h":"Social leads a digital-first mix","p":f"Social takes <b>{fmtM_(soc)}</b> ({pct_(soc,gt)}) of spend, ahead of Press at {fmtM_(press)} ({pct_(press,gt)}) — promotions-led liquor and QSR advertising favours fast, always-on digital."},
        {"h":"A defined seasonal peak","p":f"Spend peaks in <b>{d['months'][d['pk_i']]}</b> ({fmtM_(d['month_tot'][d['pk_i']])}) and bottoms out in <b>{d['months'][d['tr_i']]}</b> ({fmtM_(d['month_tot'][d['tr_i']])}) — a ~{d['swing_pct']}% swing, consistent with festive-season liquor demand."},
        {"h":"Clubs are a distinct, sizeable bloc","p":f"RSL and licensed clubs account for <b>{pct_(struct.get('Clubs & Licensed Venues',0),gt)}</b> of spend — a category-specific structure with no direct equivalent in FinTech or Travel."},
        {"h":f"{t0['advertiser']} is the runaway #1","p":f"{t0['advertiser']} alone is {fmtM_(t0['total'])} ({pct_(t0['total'],gt)}) of all measured Hospitality F&amp;B spend — more than double the next-largest advertiser."},
        {"h":"A very long, fragmented tail","p":f"The top 10 advertisers hold <b>{pct_(d['top10_sum'],gt)}</b> of spend, but {d['n_advertisers']:,} advertisers compete overall — independent venues and bottle shops fill out an unusually long tail."},
    ]

HOSPITALITY = dict(
    file="Hospitality Food & Beverage.xlsx", slug="hospitality-food-beverage", name="Hospitality Food & Beverage",
    page_title="Hospitality Food & Beverage Media Spend — Australia Aug 2025–Jul 2026",
    h1="Hospitality Food &amp; Beverage — Australian Media Spend",
    struct_title="Liquor Retail vs QSR vs Clubs", struct_kpi_label="Liquor & beverage retail share",
    struct_kpi_key="Liquor & Beverage Retail",
    struct_cap="Market structure lens — liquor &amp; beverage retail vs QSR &amp; casual dining vs clubs &amp; licensed venues vs delivery/other.",
    seg_title="Spend by Hospitality Segment", seg_note="Liquor retail chains and independent bottle shops dominate; QSR, clubs and wine specialists round out the mix.",
    structure_fn=hf_structure, category_fn=hf_category, struct_note_fn=hf_struct_note, insights_fn=hf_insights,
)

# ============================================================ RETIREMENT
RET_EXPLICIT = {
    "ingenia communities group":"Retirement Living Communities","palm lake group":"Retirement Living Communities",
    "silver chain group":"Home & Community Care","ryman healthcare australia":"Residential Aged Care",
    "aveo group":"Retirement Living Communities","levande":"Retirement Living Communities",
    "australian unity":"Health & Financial Services","arcare":"Residential Aged Care",
    "nurse next door":"Home & Community Care","right at home":"Home & Community Care",
    "lifestyle communities":"Retirement Living Communities","lincoln place":"Retirement Living Communities",
    "keyton holding":"Retirement Living Communities","baptistcare nsw & act":"Residential Aged Care",
    "retireaustralia":"Retirement Living Communities","gemlife":"Retirement Living Communities",
    "blue care":"Home & Community Care","homemade":"Home & Community Care",
    "hammondcare group":"Residential Aged Care","bolton clarke":"Residential Aged Care",
    "uniting church":"Residential Aged Care","royal freemasons":"Residential Aged Care",
    "home caring group":"Home & Community Care","benetas":"Residential Aged Care","resthaven":"Residential Aged Care",
    "living gems":"Retirement Living Communities","my guardian group":"Home & Community Care",
    "watermark chatswood projects":"Retirement Living Communities","careabout holdings":"Home & Community Care",
    "bethanie group":"Residential Aged Care","country club living":"Retirement Living Communities",
    "five good friends":"Home & Community Care","ach group":"Residential Aged Care","dovida":"Home & Community Care",
    "providence lifestyle":"Retirement Living Communities","ech":"Home & Community Care",
    "mercy health & aged care":"Residential Aged Care","arcadia group":"Retirement Living Communities",
    "lend lease primelife":"Retirement Living Communities",
}
def ret_category(name):
    n = lc(name)
    if n in RET_EXPLICIT: return RET_EXPLICIT[n]
    if any(k in n for k in ['communities','lifestyle','lend lease','gemlife','villages','estate']): return "Retirement Living Communities"
    if any(k in n for k in ['aged care','nursing','healthcare','freemasons','uniting','bethanie','mercy health','bolton clarke']): return "Residential Aged Care"
    if any(k in n for k in ['home care','nurse','caring','guardian']): return "Home & Community Care"
    if any(k in n for k in ['unity','financial','insurance','super']): return "Health & Financial Services"
    return "Other Retirement Services"

def ret_structure(name):
    cat = ret_category(name)
    if cat == "Retirement Living Communities": return "Retirement Living & Land Lease"
    if cat in ("Residential Aged Care","Home & Community Care"): return "Aged & Home Care Providers"
    return "Financial & Other Services"

def ret_struct_note(structure, gt, fmtM, pct):
    living = structure.get("Retirement Living & Land Lease", 0)
    care = structure.get("Aged & Home Care Providers", 0)
    return (f"Retirement living &amp; land lease operators spend {fmtM(living)} ({pct(living,gt)}) vs "
            f"{fmtM(care)} ({pct(care,gt)}) for aged &amp; home care providers — two distinct buyer types "
            f"competing for the same ageing-Australian audience.")

def ret_insights(d):
    ch = d['channel']; struct = d['structure']; t0 = d['t0']
    fmtM_, pct_ = d['fmtM'], d['pct']; gt = d['grand_total']
    tv = ch.get('Television',0); radio = ch.get('Radio',0)
    return [
        {"h":"Television and Radio dominate","p":f"Television takes <b>{fmtM_(tv)}</b> ({pct_(tv,gt)}) of spend, with Radio a strong second at {fmtM_(radio)} ({pct_(radio,gt)}) — a media mix aimed squarely at an older, broadcast-attentive audience."},
        {"h":"A defined seasonal pattern","p":f"Spend peaks in <b>{d['months'][d['pk_i']]}</b> ({fmtM_(d['month_tot'][d['pk_i']])}) and bottoms out in <b>{d['months'][d['tr_i']]}</b> ({fmtM_(d['month_tot'][d['tr_i']])}) — a ~{d['swing_pct']}% swing across the 12 months."},
        {"h":"Living communities lead the category","p":f"Retirement living &amp; land lease operators account for <b>{pct_(struct.get('Retirement Living & Land Lease',0),gt)}</b> of spend — the property-sale nature of the business justifies sustained brand marketing."},
        {"h":"Aged care is a fragmented, values-led field","p":f"Aged &amp; home care providers make up <b>{pct_(struct.get('Aged & Home Care Providers',0),gt)}</b> of spend across a long list of faith-based and independent operators — no single provider dominates the way living communities' leaders do."},
        {"h":f"{t0['advertiser']} leads the category","p":f"{t0['advertiser']} is the top spender at {fmtM_(t0['total'])} ({pct_(t0['total'],gt)})."},
        {"h":"A genuinely fragmented top tier","p":f"The top 10 advertisers hold only <b>{pct_(d['top10_sum'],gt)}</b> of spend across {d['n_advertisers']:,} advertisers — Retirement is one of Sunny's least concentrated measured categories."},
    ]

RETIREMENT = dict(
    file="Retirement.xlsx", slug="retirement", name="Retirement",
    page_title="Retirement Media Spend — Australia Aug 2025–Jul 2026",
    h1="Retirement — Australian Media Spend",
    struct_title="Living Communities vs Aged Care", struct_kpi_label="Aged & home care provider share",
    struct_kpi_key="Aged & Home Care Providers",
    struct_cap="Market structure lens — retirement living &amp; land lease vs aged &amp; home care providers vs financial &amp; other services.",
    seg_title="Spend by Retirement Segment", seg_note="Retirement living operators and residential/home aged care providers make up almost all measured spend.",
    structure_fn=ret_structure, category_fn=ret_category, struct_note_fn=ret_struct_note, insights_fn=ret_insights,
)

# ============================================================ SPORT TEAMS
SPORT_GOVERNING = ['afl marketing','national rugby league','cricket australia','national basketball league',
    'sanzar','australian rugby union','rugby australia','tennis australia','australian professional leagues company',
    'football australia','netball australia','volleyball australia','golf australia','sa national football league',
    'aust olympic committee','world surf league','netball nsw','australian sports foundation']
SPORT_MOTOR = ['motor culture australia','lmct plus','boating industry assoc aus','car hub australia',
    'royal automobile club of aust']
SPORT_EXPLICIT_CAT = {
    "afl marketing":"AFL","national rugby league":"NRL","cricket australia":"Cricket",
    "national basketball league":"Basketball","sanzar":"Rugby Union","tennis australia":"Other Codes & Individual Sports",
    "australian professional leagues company":"Football/Soccer","australian rugby union":"Rugby Union",
    "rugby australia":"Rugby Union","world surf league":"Other Codes & Individual Sports",
    "football australia":"Football/Soccer","manchester united":"Football/Soccer",
    "netball australia":"Other Codes & Individual Sports","volleyball australia":"Other Codes & Individual Sports",
    "st george illawarra dragons":"NRL","australian sports foundation":"Other Codes & Individual Sports",
    "brisbane lions football club":"AFL","dolphins nrl":"NRL","brisbane broncos leagues club":"NRL",
    "golf australia":"Other Codes & Individual Sports","waratahs rugby":"Rugby Union",
    "genygolf":"Other Codes & Individual Sports","sa national football league":"AFL",
    "green & gold army":"Cricket","sydney swans football club":"AFL",
    "boating industry assoc aus":"Motorsport & Non-Code Brands","penrith rugby league club":"NRL",
    "melbourne city fc":"Football/Soccer","sydney kings basketball":"Basketball",
    "port adelaide football club":"AFL","newcastle knights football clb":"NRL",
    "car hub australia":"Motorsport & Non-Code Brands","melbourne victory football club":"Football/Soccer",
    "ultimate fighting championship":"Other Codes & Individual Sports",
    "royal automobile club of aust":"Motorsport & Non-Code Brands","netball nsw":"Other Codes & Individual Sports",
    "aust olympic committee":"Other Codes & Individual Sports","motor culture australia":"Motorsport & Non-Code Brands",
    "lmct plus":"Motorsport & Non-Code Brands",
}
def sport_category(name):
    n = lc(name)
    if n in SPORT_EXPLICIT_CAT: return SPORT_EXPLICIT_CAT[n]
    if any(k in n for k in ['rugby league','nrl','dragons','broncos','knights','panthers','rabbitohs','eels','sharks','sea eagles','titans','cowboys','storm','raiders']): return "NRL"
    if any(k in n for k in ['afl','football club']) and 'fc' not in n: return "AFL"
    if any(k in n for k in [' fc',' united','victory','city fc','football federation']): return "Football/Soccer"
    if any(k in n for k in ['cricket']): return "Cricket"
    if any(k in n for k in ['rugby union','waratahs','wallabies','reds rugby','brumbies']): return "Rugby Union"
    if any(k in n for k in ['basketball']): return "Basketball"
    if any(k in n for k in ['motor','automobile','car ','boating','racing','speedway']): return "Motorsport & Non-Code Brands"
    return "Other Codes & Individual Sports"

def sport_structure(name):
    n = lc(name)
    if n in SPORT_GOVERNING: return "League & Governing Bodies"
    if n in SPORT_MOTOR: return "Motorsport & Non-Code Brands"
    cat = sport_category(name)
    if cat == "Motorsport & Non-Code Brands": return "Motorsport & Non-Code Brands"
    if cat in ("AFL","NRL","Cricket","Rugby Union","Football/Soccer","Basketball"): return "Individual Clubs"
    return "Other / Individual Sports"

def sport_struct_note(structure, gt, fmtM, pct):
    gov = structure.get("League & Governing Bodies", 0)
    clubs = structure.get("Individual Clubs", 0)
    return (f"League &amp; governing bodies (AFL, NRL, Cricket Australia, the NBL and others) spend "
            f"{fmtM(gov)} ({pct(gov,gt)}) — well ahead of individual clubs at {fmtM(clubs)} ({pct(clubs,gt)}), "
            f"which advertise locally and at a fraction of the budget.")

def sport_insights(d):
    ch = d['channel']; struct = d['structure']; t0 = d['t0']; seg = d['segment']
    fmtM_, pct_ = d['fmtM'], d['pct']; gt = d['grand_total']
    disp = ch.get('Digital Display',0); soc = ch.get('Social',0)
    afl = seg.get('AFL',0); nrl = seg.get('NRL',0)
    return [
        {"h":"Digital Display leads, not broadcast","p":f"Digital Display takes <b>{fmtM_(disp)}</b> ({pct_(disp,gt)}) of spend, ahead of Social at {fmtM_(soc)} ({pct_(soc,gt)}) — codes and clubs promote fixtures and membership drives through owned and paid digital before TV."},
        {"h":"AFL and NRL lead the codes","p":f"AFL-linked advertisers total <b>{fmtM_(afl)}</b> ({pct_(afl,gt)}) and NRL {fmtM_(nrl)} ({pct_(nrl,gt)}) — the two dominant winter codes also dominate measured media spend."},
        {"h":"A defined seasonal pattern","p":f"Spend peaks in <b>{d['months'][d['pk_i']]}</b> ({fmtM_(d['month_tot'][d['pk_i']])}) and bottoms out in <b>{d['months'][d['tr_i']]}</b> ({fmtM_(d['month_tot'][d['tr_i']])}) — a ~{d['swing_pct']}% swing tracking finals and off-season."},
        {"h":"Governing bodies outspend individual clubs","p":f"League &amp; governing bodies hold <b>{pct_(struct.get('League & Governing Bodies',0),gt)}</b> of spend — centralised competition marketing dwarfs individual club budgets."},
        {"h":f"{t0['advertiser']} is the clear #1","p":f"{t0['advertiser']} leads the category at {fmtM_(t0['total'])} ({pct_(t0['total'],gt)})."},
        {"h":"A wide, multi-code tail","p":f"The top 10 advertisers hold <b>{pct_(d['top10_sum'],gt)}</b> of spend across {d['n_advertisers']:,} advertisers spanning AFL, NRL, cricket, rugby, football, basketball and individual sports."},
    ]

SPORT_TEAMS = dict(
    file="Sport Teams.xlsx", slug="sport-teams", name="Sport Teams",
    page_title="Sport Teams Media Spend — Australia Aug 2025–Jul 2026",
    h1="Sport Teams — Australian Media Spend",
    struct_title="Governing Bodies vs Individual Clubs", struct_kpi_label="League & governing body share",
    struct_kpi_key="League & Governing Bodies",
    struct_cap="Market structure lens — league &amp; governing bodies vs individual clubs vs motorsport &amp; non-code brands.",
    seg_title="Spend by Sporting Code", seg_note="AFL and NRL lead measured spend, with cricket, rugby union, football and basketball filling out the field.",
    structure_fn=sport_structure, category_fn=sport_category, struct_note_fn=sport_struct_note, insights_fn=sport_insights,
)

# ============================================================ FINTECH (rebuild for full-list consistency)
import json as _json
FT_KNOWN = {}
try:
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "fintech_known.json")) as f:
        FT_KNOWN = _json.load(f)
except FileNotFoundError:
    pass

FT_BIG_BANK = ['westpac','commonwealth bank','anz bank','national australia bank',' nab ','ing group','ing bank',
    'bankwest','macquarie bank','suncorp bank','bank of queensland','bendigo & adelaide bank','bendigo bank']
FT_NEOBANK = ['revolut','up bank','86 400','judo bank','volt bank','xinja','alex bank']
FT_PAYMENTS_BNPL = ['paypal','afterpay','square au','square inc','zip co','zip money','zipmoney','klarna',
    'humm group','openpay','tyro payments','airwallex','zeller','payoneer','sezzle','laybuy']
FT_TRADING = ['etoro','ig markets','cmc markets','mitrade','plus500','interactive brokers','pepperstone',
    'stakeshop','stake pty',' stake ','futu securities','capital com sv','saxo','superhero','selfwealth',
    'commsec','nabtrade','bell direct','tiger brokers','moomoo']
FT_COMPARISON = ['compare club','finder.com','canstar','mozo','iselect','comparethemarket','ratecity']
FT_CRYPTO = ['coinspot','crypto.com','swyftx','independent reserve','ripple','binance','coinbase','btc markets',
    'digital surge','kraken','coinjar','bitaroo']
FT_WEALTH = ['la trobe financial','mcmillan shakespeare','lgt crestone','colonial first state','amp limited',
    'hub24','netwealth','perpetual','pendal','magellan financial','platinum asset']
FT_MONEY_TRANSFER = ['remitly','wise','western union','moneygram','ria financial','instarem','orbit remit',
    'xe money','currencyfair','worldremit']
FT_CREDIT_LENDING = ['ipf digital','credit corp','moneyme','prospa','latitude financial','swoosh finance',
    'loans.com','on deck capital','pepper group','now finance','wisr','harmoney','plenti','beforepay',
    'cigno','jacaranda finance']
FT_PAYMENTS_INFRA = ['australian payments plus','eftpos australia','assembly payments','payright','cuscal']
FT_INSURANCE = ['australian unity','aami','budget direct','youi','qbe insurance','allianz','nrma insurance',
    'medibank','bupa','hcf ','nib health']
FT_PROFESSIONAL = ['pricewaterhousecoopers','kpmg','deloitte','ernst & young',' ey ','h&r block','etax',
    'itp accounting','taxfp']

def ft_category(name):
    n = lc(name)
    if n in FT_KNOWN: return FT_KNOWN[n][0]
    if any(k in n for k in FT_BIG_BANK): return "Big Bank"
    if any(k in n for k in FT_NEOBANK): return "Neobank / Digital Bank"
    if any(k in n for k in FT_PAYMENTS_BNPL): return "Payments & BNPL"
    if any(k in n for k in FT_TRADING): return "Trading & Investing"
    if any(k in n for k in FT_COMPARISON): return "Comparison / Aggregator"
    if any(k in n for k in FT_CRYPTO): return "Crypto"
    if any(k in n for k in FT_WEALTH): return "Wealth, Super & Advice"
    if any(k in n for k in FT_MONEY_TRANSFER): return "Money Transfer"
    if any(k in n for k in FT_CREDIT_LENDING): return "Credit & Lending"
    if any(k in n for k in FT_PAYMENTS_INFRA): return "Payments Infrastructure"
    if any(k in n for k in FT_INSURANCE): return "Insurance"
    if any(k in n for k in FT_PROFESSIONAL): return "Professional Services"
    return "Other Financial Services"

def ft_structure(name):
    n = lc(name)
    if n in FT_KNOWN: return FT_KNOWN[n][1]
    seg = ft_category(name)
    if seg in ("Big Bank", "Wealth, Super & Advice", "Insurance"): return "Incumbent"
    if seg == "Professional Services": return "Professional Services"
    if seg == "Other Financial Services": return "Other"
    return "Challenger / Fintech"

def ft_struct_note(structure, gt, fmtM, pct):
    challenger = structure.get("Challenger / Fintech", 0)
    incumbent = structure.get("Incumbent", 0)
    return (f"Challenger / fintech brands outspend incumbent banks & insurers {fmtM(challenger)} to "
            f"{fmtM(incumbent)} — digital-native players are buying media at scale.")

def ft_insights(d):
    ch = d['channel']; struct = d['structure']; seg = d['segment']; t0 = d['t0']
    fmtM_, pct_ = d['fmtM'], d['pct']; gt = d['grand_total']
    soc = ch.get('Social', 0); disp = ch.get('Digital Display', 0)
    challenger = struct.get('Challenger / Fintech', 0); incumbent = struct.get('Incumbent', 0)
    payBnpl = seg.get('Payments & BNPL', 0)
    return [
        {"h":"Social & digital lead, not press","p":f"Social (<b>{fmtM_(soc)}</b>, {pct_(soc,gt)}) and Digital Display ({fmtM_(disp)}, {pct_(disp,gt)}) together take almost two-thirds of category spend — a sharp contrast to travel's press-led mix."},
        {"h":"A defined seasonal dip","p":f"Spend peaks in <b>{d['months'][d['pk_i']]}</b> ({fmtM_(d['month_tot'][d['pk_i']])}) and bottoms out in <b>{d['months'][d['tr_i']]}</b> ({fmtM_(d['month_tot'][d['tr_i']])}) — a ~{d['swing_pct']}% swing across the 12 months (excl. the partial July read)."},
        {"h":"Challengers outspend incumbents","p":f"Challenger/fintech brands account for <b>{pct_(challenger,gt)}</b> of spend vs <b>{pct_(incumbent,gt)}</b> for Big Banks & incumbents — digital-native players are buying media aggressively to build share."},
        {"h":"A long, fragmented tail","p":f"The top 10 advertisers hold <b>{pct_(d['top10_sum'],gt)}</b> of spend, but {d['n_advertisers']:,} advertisers compete overall — FinTech is concentrated at the top yet highly fragmented below."},
        {"h":"Payments & BNPL punch hard","p":f"Payments & BNPL players spent <b>{fmtM_(payBnpl)}</b> — {t0['advertiser']} alone is the single largest spender at {fmtM_(t0['total'])} ({pct_(t0['total'],gt)})."},
        {"h":"Out of Home is a real channel here","p":f"FinTech puts <b>{fmtM_(ch.get('Out of Home',0))}</b> ({pct_(ch.get('Out of Home',0),gt)}) into OOH — well above travel's mix-adjusted share, reflecting trust-building brand campaigns from banks and trading platforms."},
    ]

FINTECH = dict(
    file="FinTech.xlsx", slug="fintech", name="FinTech",
    page_title="FinTech Media Spend — Australia Aug 2025–Jul 2026",
    h1="FinTech — Australian Media Spend",
    struct_title="Incumbent vs Challenger", struct_kpi_label="Challenger / fintech share",
    struct_kpi_key="Challenger / Fintech",
    struct_cap="Market structure lens — traditional banks/insurers vs digital-native fintech challengers vs professional services.",
    seg_title="Spend by FinTech Segment", seg_note="Banks, payments/BNPL and trading platforms dominate; comparison sites and money transfer punch above their spend via always-on digital.",
    structure_fn=ft_structure, category_fn=ft_category, struct_note_fn=ft_struct_note, insights_fn=ft_insights,
)

ALL_VERTICALS = [MOTOR_VEHICLES, AGRICULTURE, HOSPITALITY, RETIREMENT, SPORT_TEAMS]

if __name__ == "__main__":
    for v in ALL_VERTICALS:
        DATA = build(v)
        render(v, DATA)
