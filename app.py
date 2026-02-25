import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timezone, timedelta
import itertools
import random

# --- 1. CONFIGURATIE ---
st.set_page_config(page_title="Pro Punter Dashboard", page_icon="⚖️", layout="wide")
API_KEY = 'ae33f20cd78d0b2b015703ded3330fcb'
SHEET_URL = "https://docs.google.com/spreadsheets/d/10F4xl7dcHIpfN1xdLrZ2BNAn532OJk0_58ErD51rRE4/edit?usp=sharing"

st.title("⚖️ Professional Multi-Sport Generator")
st.markdown(f"**Gekoppeld aan:** [Pro Bet Tracker]({SHEET_URL})")

# Markten en Sporten
ALL_SPORTS = {
    "Voetbal": ["soccer_uefa_champs_league", "soccer_epl", "soccer_spain_la_liga", "soccer_germany_bundesliga", "soccer_italy_serie_a", "soccer_netherlands_eredivisie", "soccer_belgium_first_division", "soccer_portugal_primeira_liga"],
    "Basketbal": ["basketball_nba", "basketball_euroleague"],
    "Tennis": ["tennis_atp_dubai", "tennis_atp_acapulco"],
    "Extra": ["darts_pdc_world_championship", "icehockey_nhl"]
}

if 'pool' not in st.session_state: st.session_state.pool = []
if 'export_data' not in st.session_state: st.session_state.export_data = []

# --- 2. DE SCANNER ---
def run_full_scan():
    matches = []
    now = datetime.now(timezone.utc)
    # Ruime marge: Alles wat binnen nu en 30 uur begint
    time_limit = now + timedelta(hours=30)
    
    with st.spinner("Markten scannen op safe-bets, BTTS en Goals..."):
        for category, keys in ALL_SPORTS.items():
            for key in keys:
                url = f"https://api.the-odds-api.com/v4/sports/{key}/odds/"
                # H2H voor favorieten, BTTS en Totals voor goals
                params = {'apiKey': API_KEY, 'regions': 'eu', 'markets': 'h2h,btts,totals', 'oddsFormat': 'decimal'}
                try:
                    r = requests.get(url, params=params)
                    if r.status_code == 200:
                        data = r.json()
                        for game in data:
                            m_time = datetime.fromisoformat(game['commence_time'].replace('Z', '+00:00'))
                            if now <= m_time <= time_limit:
                                if game.get('bookmakers'):
                                    bm = game['bookmakers'][0]
                                    for market in bm['markets']:
                                        for outcome in market['outcomes']:
                                            price = outcome['price']
                                            # Professionele Safe Range
                                            if 1.10 <= price <= 1.60:
                                                label = ""
                                                if market['key'] == 'h2h': label = f"Win: {outcome['name']}"
                                                elif market['key'] == 'btts': label = f"BTTS: {outcome['name']}"
                                                elif market['key'] == 'totals': label = f"Goals: {outcome['name']} {outcome.get('point','')}"
                                                
                                                matches.append({
                                                    "Sport": category, "Datum": m_time.strftime("%d-%m-%Y"),
                                                    "Tijd": m_time.strftime("%H:%M"), "Match": f"{game['home_team']} - {game['away_team']}",
                                                    "Keuze": label, "Odd": price
                                                })
                except: continue
    return matches

# --- 3. UI CONTROLS ---
with st.sidebar:
    st.header("⚙️ Instellingen")
    if st.button("🚀 START SCAN"):
        st.session_state.pool = run_full_scan()
        st.success(f"{len(st.session_state.pool)} opties geladen!")

    st.divider()
    if st.session_state.pool:
        if st.button("📋 GENEREER DAGELIJKSE 4 SLIPS"):
            st.session_state.export_data = [] # Reset voor nieuwe generatie
            for target in [1.5, 2.0, 3.0, 5.0]:
                pool_sample = random.sample(st.session_state.pool, min(60, len(st.session_state.pool)))
                best_combo, closest_diff = None, 999
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
                    # Witregel tussen slips
                    st.session_state.export_data.append({k: "" for k in ["Slip_ID", "Match_Datum", "Tijd", "Wedstrijd", "Keuze", "Odd", "Status"]})
            st.rerun()

# --- 4. OUTPUT ---
if st.session_state.export_data:
    st.subheader("📑 Jouw Professionele Slips")
    df_export = pd.DataFrame(st.session_state.export_data)
    st.dataframe(df_export, height=500)
    
    csv = df_export.to_csv(index=False).encode('utf-8')
    st.download_button("📥 DOWNLOAD VOOR PRO BET TRACKER", csv, "dagelijkse_bets.csv", "text/csv")
    
    if st.button("🗑️ Wis Resultaten"):
        st.session_state.export_data = []
        st.rerun()
elif st.session_state.pool:
    st.info(f"Er staan {len(st.session_state.pool)} wedstrijden klaar in de wachtrij. Klik op 'Genereer' in de zijbalk.")
