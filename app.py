import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import itertools
import random

# --- CONFIGURATIE ---
st.set_page_config(page_title="Pro Multi-Market Generator", page_icon="⚽", layout="wide")
API_KEY = 'ae33f20cd78d0b2b015703ded3330fcb'
SHEET_URL = "https://docs.google.com/spreadsheets/d/10F4xl7dcHIpfN1xdLrZ2BNAn532OJk0_58ErD51rRE4/edit?usp=sharing"
VANDAAG_STR = "2026-02-25"

st.title("⚖️ Professional Multi-Market Generator")
st.markdown(f"**Markten:** H2H, BTTS, Over/Under, Team Goals | **Datum:** {VANDAAG_STR}")

# --- SPORT CONFIG ---
ALL_SPORTS = {
    "Voetbal": ["soccer_epl", "soccer_uefa_champs_league", "soccer_netherlands_eredivisie", "soccer_spain_la_liga", "soccer_germany_bundesliga", "soccer_italy_serie_a"],
    "Tennis": ["tennis_atp_dubai", "tennis_wta_doha"],
    "Basketbal": ["basketball_nba", "basketball_euroleague"]
}

if 'pool' not in st.session_state: st.session_state.pool = []
if 'export_data' not in st.session_state: st.session_state.export_data = []

# --- DIEPE SCANNER ---
def deep_scan():
    matches = []
    # We voegen de specifieke markten toe aan de API call
    markets = "h2h,btts,totals" 
    
    with st.spinner("Analyseren van Goals, BTTS en H2H markten..."):
        for category, keys in ALL_SPORTS.items():
            for key in keys:
                url = f"https://api.the-odds-api.com/v4/sports/{key}/odds/"
                params = {'apiKey': API_KEY, 'regions': 'eu', 'markets': markets, 'oddsFormat': 'decimal'}
                try:
                    r = requests.get(url, params=params)
                    if r.status_code == 200:
                        for game in r.json():
                            if VANDAAG_STR in game['commence_time']:
                                dt = datetime.fromisoformat(game['commence_time'].replace('Z', ''))
                                if game['bookmakers']:
                                    bm = game['bookmakers'][0]
                                    for market in bm['markets']:
                                        for outcome in market['outcomes']:
                                            price = outcome['price']
                                            
                                            # Filter op professional safe range
                                            if 1.10 <= price <= 1.55:
                                                m_name = ""
                                                # Markten hernoemen voor overzicht
                                                if market['key'] == 'h2h': m_name = f"Win: {outcome['name']}"
                                                elif market['key'] == 'btts': m_name = f"BTTS: {outcome['name']}"
                                                elif market['key'] == 'totals': m_name = f"Goals: {outcome['name']} {outcome['point']}"
                                                
                                                matches.append({
                                                    "Sport": category, "Datum": dt.strftime("%d-%m-%Y"), 
                                                    "Tijd": dt.strftime("%H:%M"), "Match": f"{game['home_team']} - {game['away_team']}", 
                                                    "Keuze": m_name, "Odd": price
                                                })
                except: continue
    return pd.DataFrame(matches).drop_duplicates(subset=['Match', 'Keuze']).to_dict('records')

# --- UI CONTROLS ---
with st.sidebar:
    st.header("⚙️ Instellingen")
    if st.button("🚀 UPDATE LIVE DATA"):
        st.session_state.pool = deep_scan()
        st.success(f"{len(st.session_state.pool)} kansen gevonden!")

    st.divider()
    random_btn = st.button("🎲 RANDOM SAFE BET")
    standard_btn = st.button("📋 GENERATE DAILY 4")

# --- GENERATIE LOGICA ---
if random_btn and st.session_state.pool:
    selection = random.sample(st.session_state.pool, min(3, len(st.session_state.pool)))
    total_odd = 1.0
    st.subheader("🎲 Random Deep-Market Selection")
    for s in selection:
        total_odd *= s['Odd']
        st.write(f"🔹 {s['Tijd']} | **{s['Match']}** | {s['Keuze']} (@{s['Odd']})")
        st.session_state.export_data.append({"Slip_ID": f"RANDOM (@{round(total_odd,2)})", "Match_Datum": s['Datum'], "Tijd": s['Tijd'], "Wedstrijd": f"[{s['Sport']}] {s['Match']}", "Keuze": s['Keuze'], "Odd": s['Odd'], "Status": "OPEN"})
    st.session_state.export_data.append({k: "" for k in ["Slip_ID", "Match_Datum", "Tijd", "Wedstrijd", "Keuze", "Odd", "Status"]})

if standard_btn and st.session_state.pool:
    cols = st.columns(4)
    for idx, target in enumerate([1.5, 2.0, 3.0, 5.0]):
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
                    st.write(f"⏱ {m['Tijd']} | {m['Keuze']}\n{m['Match']}")
                    st.session_state.export_data.append({"Slip_ID": f"Target {target} (@{f_odd})", "Match_Datum": m['Datum'], "Tijd": m['Tijd'], "Wedstrijd": f"[{m['Sport']}] {m['Match']}", "Keuze": m['Keuze'], "Odd": m['Odd'], "Status": "OPEN"})
                st.session_state.export_data.append({k: "" for k in ["Slip_ID", "Match_Datum", "Tijd", "Wedstrijd", "Keuze", "Odd", "Status"]})

# --- DOWNLOAD ---
if st.session_state.export_data:
    csv = pd.DataFrame(st.session_state.export_data).to_csv(index=False).encode('utf-8')
    st.download_button("📥 DOWNLOAD VOOR PRO BET TRACKER", csv, f"multi_market_{VANDAAG_STR}.csv", "text/csv")
