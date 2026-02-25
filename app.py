import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timezone
import itertools
import random

# --- CONFIGURATIE ---
st.set_page_config(page_title="Ultimate Pro Punter", page_icon="🌍", layout="wide")
API_KEY = 'ae33f20cd78d0b2b015703ded3330fcb'
SHEET_URL = "https://docs.google.com/spreadsheets/d/10F4xl7dcHIpfN1xdLrZ2BNAn532OJk0_58ErD51rRE4/edit?usp=sharing"

st.title("🌍 Ultimate Multi-Sport & Market Generator")
st.markdown(f"**Admin:** [Pro Bet Tracker]({SHEET_URL})")

# MAXIMALE LIJST VAN COMPETITIES
ALL_SPORTS_EXPANDED = {
    "Voetbal Elite": ["soccer_uefa_champs_league", "soccer_epl", "soccer_spain_la_liga", "soccer_germany_bundesliga", "soccer_italy_serie_a", "soccer_france_ligue_1"],
    "Voetbal Sub": ["soccer_netherlands_eredivisie", "soccer_belgium_first_division", "soccer_portugal_primeira_liga", "soccer_turkey_super_lig", "soccer_efl_championship", "soccer_brazil_campeonato", "soccer_mexico_mx"],
    "Basketbal": ["basketball_nba", "basketball_euroleague", "basketball_ncaab", "basketball_spain_acb", "basketball_turkey_tbsl"],
    "Tennis": ["tennis_atp_dubai", "tennis_atp_acapulco", "tennis_wta_doha", "tennis_wta_austin"],
    "IJshockey": ["icehockey_nhl", "icehockey_sweden_allsvenskan", "icehockey_finland_liiga", "icehockey_germany_del"],
    "Overig": ["darts_pdc_world_championship", "handball_bundesliga", "volleyball_italy_superlega", "rugbyleague_nrl"]
}

if 'pool' not in st.session_state: st.session_state.pool = []
if 'export_data' not in st.session_state: st.session_state.export_data = []

def ultra_scan():
    matches = []
    now = datetime.now(timezone.utc)
    
    # We scannen op H2H, BTTS en Totals (Goals)
    markets = "h2h,btts,totals"
    
    with st.spinner("Bezig met een massale scan van alle wereldwijde markten..."):
        for category, keys in ALL_SPORTS_EXPANDED.items():
            for key in keys:
                url = f"https://api.the-odds-api.com/v4/sports/{key}/odds/"
                params = {'apiKey': API_KEY, 'regions': 'eu', 'markets': markets, 'oddsFormat': 'decimal'}
                try:
                    r = requests.get(url, params=params)
                    if r.status_code == 200:
                        data = r.json()
                        for game in data:
                            match_time = datetime.fromisoformat(game['commence_time'].replace('Z', '+00:00'))
                            
                            # Filter: Moet vandaag zijn en nog niet begonnen
                            if match_time > now and match_time.date() == now.date():
                                if game['bookmakers']:
                                    bm = game['bookmakers'][0]
                                    for market in bm['markets']:
                                        for outcome in market['outcomes']:
                                            price = outcome['price']
                                            
                                            # Professional Safe Range: 1.10 - 1.60 (iets ruimer voor meer resultaten)
                                            if 1.10 <= price <= 1.60:
                                                m_type = ""
                                                if market['key'] == 'h2h': m_type = f"Win: {outcome['name']}"
                                                elif market['key'] == 'btts': m_type = f"BTTS: {outcome['name']}"
                                                elif market['key'] == 'totals': m_type = f"Goals: {outcome['name']} {outcome['point']}"
                                                
                                                matches.append({
                                                    "Sport": category.split()[0],
                                                    "Datum": match_time.strftime("%d-%m-%Y"),
                                                    "Tijd": match_time.strftime("%H:%M"),
                                                    "Match": f"{game['home_team']} - {game['away_team']}",
                                                    "Keuze": m_type,
                                                    "Odd": price
                                                })
                except: continue
    return matches

# --- UI ---
with st.sidebar:
    st.header("⚙️ Controle Paneel")
    if st.button("🚀 START MASSALE SCAN"):
        st.session_state.pool = ultra_scan()
        st.success(f"{len(st.session_state.pool)} kansen gevonden!")

    st.divider()
    if st.session_state.pool:
        st.button("🎲 RANDOM SAFE BET", on_click=lambda: gen_random())
        st.button("📋 GENERATE DAILY 4", on_click=lambda: gen_standard())

# --- GENERATIE FUNCTIES ---
def gen_random():
    if len(st.session_state.pool) >= 3:
        selection = random.sample(st.session_state.pool, 3)
        total_odd = 1.0
        for s in selection: total_odd *= s['Odd']
        
        for s in selection:
            st.session_state.export_data.append({
                "Slip_ID": f"RANDOM (@{round(total_odd,2)})", "Match_Datum": s['Datum'], "Tijd": s['Tijd'], 
                "Wedstrijd": f"[{s['Sport']}] {s['Match']}", "Keuze": s['Keuze'], "Odd": s['Odd'], "Status": "OPEN"
            })
        st.session_state.export_data.append({k: "" for k in ["Slip_ID", "Match_Datum", "Tijd", "Wedstrijd", "Keuze", "Odd", "Status"]})

def gen_standard():
    for target in [1.5, 2.0, 3.0, 5.0]:
        best_combo, closest_diff = None, 999
        # Gebruik een subset van de pool voor snelheid bij grote data
        pool_sample = random.sample(st.session_state.pool, min(50, len(st.session_state.pool)))
        for r in range(2, 5):
            for combo in itertools.combinations(pool_sample, r):
                total = 1.0
                for m in combo: total *= m['Odd']
                if total >= target and abs(total - target) < closest_diff and total <= (target * 1.3):
                    closest_diff = abs(total - target)
                    best_combo, f_odd = combo, round(total, 2)
        
        if best_combo:
            for m in best_combo:
                st.session_state.export_data.append({
                    "Slip_ID": f"Target {target} (@{f_odd})", "Match_Datum": m['Datum'], "Tijd": m['Tijd'], 
                    "Wedstrijd": f"[{m['Sport']}] {m['Match']}", "Keuze": m['Keuze'], "Odd": m['Odd'], "Status": "OPEN"
                })
            st.session_state.export_data.append({k: "" for k in ["Slip_ID", "Match_Datum", "Tijd", "Wedstrijd", "Keuze", "Odd", "Status"]})

# --- DOWNLOAD SECTIE ---
if st.session_state.export_data:
    st.subheader("📑 Klaar voor Import")
    df_export = pd.DataFrame(st.session_state.export_data)
    st.table(df_export.head(10)) # Toon een preview
    csv = df_export.to_csv(index=False).encode('utf-8')
    st.download_button("📥 DOWNLOAD CSV VOOR GOOGLE SHEETS", csv, "pro_punter_export.csv", "text/csv")
