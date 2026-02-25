import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import itertools
import random

# --- CONFIGURATIE ---
st.set_page_config(page_title="Global Multi-Sport Punter", page_icon="⚖️", layout="wide")
API_KEY = 'ae33f20cd78d0b2b015703ded3330fcb'
SHEET_URL = "https://docs.google.com/spreadsheets/d/10F4xl7dcHIpfN1xdLrZ2BNAn532OJk0_58ErD51rRE4/edit?usp=sharing"

st.title("⚖️ Global Multi-Sport Betting System")
st.markdown(f"**Admin:** [Pro Bet Tracker]({SHEET_URL})")

# Alle beschikbare sport-keys voor een brede scan
ALL_SPORTS = {
    "Voetbal": ["soccer_epl", "soccer_uefa_champs_league", "soccer_netherlands_eredivisie", "soccer_spain_la_liga", "soccer_germany_bundesliga", "soccer_italy_serie_a", "soccer_belgium_first_division"],
    "Tennis": ["tennis_atp_dubai", "tennis_wta_doha"],
    "Basketbal": ["basketball_nba", "basketball_euroleague"],
    "IJshockey": ["icehockey_nhl"],
    "Darts": ["darts_pdc_world_championship"],
    "Handbal": ["handball_bundesliga"],
    "Rugby": ["rugbyleague_nrl"]
}

if 'pool' not in st.session_state: st.session_state.pool = []
if 'export_data' not in st.session_state: st.session_state.export_data = []

# --- SCANNER FUNCTIE ---
def scan_markets():
    matches = []
    with st.spinner("Wereldwijde markten scannen op safe bets..."):
        for category, keys in ALL_SPORTS.items():
            for key in keys:
                url = f"https://api.the-odds-api.com/v4/sports/{key}/odds/"
                params = {'apiKey': API_KEY, 'regions': 'eu', 'markets': 'h2h,totals', 'oddsFormat': 'decimal'}
                try:
                    r = requests.get(url, params=params)
                    if r.status_code == 200:
                        for game in r.json():
                            dt = datetime.fromisoformat(game['commence_time'].replace('Z', ''))
                            if game['bookmakers']:
                                for market in game['bookmakers'][0]['markets']:
                                    for outcome in market['outcomes']:
                                        if 1.10 <= outcome['price'] <= 1.45:
                                            label = f"{outcome['name']}" if market['key'] == 'h2h' else f"{outcome['name']} {outcome.get('point','')}"
                                            matches.append({
                                                "Sport": category, "Datum": dt.strftime("%d-%m-%Y"), "Tijd": dt.strftime("%H:%M"),
                                                "Match": f"{game['home_team']} - {game['away_team']}", "Keuze": label, "Odd": outcome['price']
                                            })
                except: continue
    return pd.DataFrame(matches).drop_duplicates(subset=['Match', 'Keuze']).to_dict('records')

# --- SIDEBAR & ACTIES ---
with st.sidebar:
    st.header("⚙️ Bediening")
    if st.button("🚀 1. UPDATE MARKT DATA"):
        st.session_state.pool = scan_markets()
        st.success(f"{len(st.session_state.pool)} safe bets geladen!")

    st.divider()
    random_btn = st.button("🎲 2. RANDOM SAFE BET (3-FOLD)")
    standard_btn = st.button("📋 3. GENEREER DE 4 STANDAARD SLIPS")

# --- RANDOM GENERATOR ---
if random_btn and st.session_state.pool:
    st.subheader("🎲 Random Multi-Sport Safe Selection")
    # Kies 3 willekeurige bets uit verschillende sporten indien mogelijk
    selection = random.sample(st.session_state.pool, min(3, len(st.session_state.pool)))
    total_odd = 1.0
    for s in selection: total_odd *= s['Odd']
    
    col_r = st.columns(1)
    with col_r[0]:
        st.warning(f"**Random Slip @{round(total_odd, 2)}**")
        for s in selection:
            st.write(f"🏷️ {s['Sport']} | {s['Datum']} {s['Tijd']} | **{s['Match']}** ({s['Keuze']} @{s['Odd']})")
            st.session_state.export_data.append({"Slip_ID": f"RANDOM (@{round(total_odd,2)})", "Match_Datum": s['Datum'], "Tijd": s['Tijd'], "Wedstrijd": f"[{s['Sport']}] {s['Match']}", "Keuze": s['Keuze'], "Odd": s['Odd'], "Status": "OPEN"})
        st.session_state.export_data.append({k: "" for k in ["Slip_ID", "Match_Datum", "Tijd", "Wedstrijd", "Keuze", "Odd", "Status"]})

# --- STANDAARD GENERATOR ---
if standard_btn and st.session_state.pool:
    st.subheader("📑 Professionele Dagelijkse Slips")
    cols = st.columns(4)
    targets = [1.5, 2.0, 3.0, 5.0]
    
    for idx, target in enumerate(targets):
        best_combo, closest_diff = None, 999
        for r in range(2, 5):
            for combo in itertools.combinations(st.session_state.pool, r):
                total = 1.0
                for m in combo: total *= m['Odd']
                if total >= target and abs(total - target) < closest_diff and total <= (target * 1.3):
                    closest_diff = abs(total - target)
                    best_combo, f_odd = combo, round(total, 2)
        
        with cols[idx]:
            if best_combo:
                st.info(f"**Target {target} (@{f_odd})**")
                for m in best_combo:
                    st.write(f"📅 {m['Datum']} | {m['Tijd']}\n{m['Match']}\n`{m['Keuze']} @{m['Odd']}`")
                    st.session_state.export_data.append({"Slip_ID": f"Target {target} (@{f_odd})", "Match_Datum": m['Datum'], "Tijd": m['Tijd'], "Wedstrijd": f"[{m['Sport']}] {m['Match']}", "Keuze": m['Keuze'], "Odd": m['Odd'], "Status": "OPEN"})
                st.session_state.export_data.append({k: "" for k in ["Slip_ID", "Match_Datum", "Tijd", "Wedstrijd", "Keuze", "Odd", "Status"]})
            else: st.error(f"Geen combo voor {target}")

# --- EXPORT ---
if st.session_state.export_data:
    st.divider()
    csv = pd.DataFrame(st.session_state.export_data).to_csv(index=False).encode('utf-8')
    st.download_button("📥 DOWNLOAD VOOR PRO BET TRACKER", csv, "pro_bets.csv", "text/csv")
    if st.button("🗑️ Wis export-wachtrij"): 
        st.session_state.export_data = []
        st.rerun()
