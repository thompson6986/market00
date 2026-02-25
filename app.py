import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timezone, timedelta
import itertools
import random

# --- 1. CONFIGURATIE ---
st.set_page_config(page_title="Ultimate Pro Punter V3", page_icon="⚖️", layout="wide")
API_KEY = 'ae33f20cd78d0b2b015703ded3330fcb'
SHEET_URL = "https://docs.google.com/spreadsheets/d/10F4xl7dcHIpfN1xdLrZ2BNAn532OJk0_58ErD51rRE4/edit?usp=sharing"

st.title("⚖️ Professional Multi-Market Generator V3")
st.markdown(f"**Admin:** [Pro Bet Tracker]({SHEET_URL}) | **Focus:** Favorieten, BTTS & Goals")

# MAXIMALE LIJST VAN COMPETITIES
ALL_SPORTS_EXPANDED = {
    "Voetbal Elite": ["soccer_uefa_champs_league", "soccer_epl", "soccer_spain_la_liga", "soccer_germany_bundesliga", "soccer_italy_serie_a", "soccer_france_ligue_1"],
    "Voetbal Sub": ["soccer_netherlands_eredivisie", "soccer_belgium_first_division", "soccer_portugal_primeira_liga", "soccer_turkey_super_lig", "soccer_efl_championship", "soccer_brazil_campeonato"],
    "Basketbal": ["basketball_nba", "basketball_euroleague"],
    "Tennis": ["tennis_atp_dubai", "tennis_atp_acapulco", "tennis_wta_doha"],
    "IJshockey": ["icehockey_nhl"],
    "Extra": ["darts_pdc_world_championship", "handball_bundesliga"]
}

if 'pool' not in st.session_state: st.session_state.pool = []
if 'export_data' not in st.session_state: st.session_state.export_data = []

# --- 2. DE "FAVORIET & GOALS" SCANNER ---
def ultra_scan_v3():
    matches = []
    now = datetime.now(timezone.utc)
    one_day_later = now + timedelta(days=1)
    
    # We vragen H2H, BTTS en Totals op
    markets = "h2h,btts,totals"
    
    with st.spinner("Scannen van Favorieten, BTTS en Goal markten..."):
        for category, keys in ALL_SPORTS_EXPANDED.items():
            for key in keys:
                url = f"https://api.the-odds-api.com/v4/sports/{key}/odds/"
                params = {'apiKey': API_KEY, 'regions': 'eu', 'markets': markets, 'oddsFormat': 'decimal'}
                try:
                    r = requests.get(url, params=params)
                    data = r.json()
                    if isinstance(data, list):
                        for game in data:
                            match_time = datetime.fromisoformat(game['commence_time'].replace('Z', '+00:00'))
                            
                            # FILTER: Volgende 24 uur
                            if now <= match_time <= one_day_later:
                                if game.get('bookmakers'):
                                    bm = game['bookmakers'][0]
                                    for market in bm['markets']:
                                        for outcome in market['outcomes']:
                                            price = outcome['price']
                                            
                                            # Professional Safe Range: 1.10 - 1.65
                                            if 1.10 <= price <= 1.65:
                                                m_type = ""
                                                # Markten hernoemen voor je Sheet
                                                if market['key'] == 'h2h':
                                                    # Favoriet scoort logica: als odd laag is, is de kans op een goal groot
                                                    m_type = f"Winst (Favoriet): {outcome['name']}"
                                                elif market['key'] == 'btts':
                                                    m_type = f"BTTS: {outcome['name']}"
                                                elif market['key'] == 'totals':
                                                    m_type = f"Goals: {outcome['name']} {outcome.get('point','')}"
                                                
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

# --- 3. UI ---
with st.sidebar:
    st.header("⚙️ Controle Paneel")
    if st.button("🚀 START SCAN (VOLGENDE 24U)"):
        st.session_state.pool = ultra_scan_v3()
        if st.session_state.pool:
            st.success(f"{len(st.session_state.pool)} kansen gevonden!")
        else:
            st.error("0 gevonden. Probeer over enkele minuten opnieuw.")

    st.divider()
    if st.session_state.pool:
        if st.button("🎲 RANDOM SAFE BET"):
            selection = random.sample(st.session_state.pool, min(3, len(st.session_state.pool)))
            total_odd = 1.0
            for s in selection: total_odd *= s['Odd']
            for s in selection:
                st.session_state.export_data.append({
                    "Slip_ID": f"RANDOM (@{round(total_odd,2)})", "Match_Datum": s['Datum'], "Tijd": s['Tijd'], 
                    "Wedstrijd": f"[{s['Sport']}] {s['Match']}", "Keuze": s['Keuze'], "Odd": s['Odd'], "Status": "OPEN"
                })
            st.session_state.export_data.append({k: "" for k in ["Slip_ID", "Match_Datum", "Tijd", "Wedstrijd", "Keuze", "Odd", "Status"]})
            st.rerun()

        if st.button("📋 GENERATE DAILY 4"):
            for target in [1.5, 2.0, 3.0, 5.0]:
                best_combo, closest_diff = None, 999
                # Sample voor stabiliteit
                pool_sample = random.sample(st.session_state.pool, min(70, len(st.session_state.pool)))
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
            st.rerun()

# --- 4. EXPORT ---
if st.session_state.export_data:
    df_export = pd.DataFrame(st.session_state.export_data)
    st.table(df_export.head(15))
    csv = df_export.to_csv(index=False).encode('utf-8')
    st.download_button("📥 DOWNLOAD CSV VOOR GOOGLE SHEETS", csv, "pro_punter_export.csv", "text/csv")
    if st.button("🗑️ Wis lijst"):
        st.session_state.export_data = []
        st.rerun()
