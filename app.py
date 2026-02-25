import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timezone, timedelta
import itertools
import random

# --- 1. CONFIGURATIE ---
st.set_page_config(page_title="Pro Punter Dashboard", page_icon="⚖️", layout="wide")
API_KEY = 'ae33f20cd78d0b2b015703ded3330fcb'

st.title("⚖️ Professional Multi-Market Generator")
st.caption("Status: Verbinding Actief | Tijdvrij Scannen")

# De sporten die we zojuist succesvol hebben gescand
LEAGUES = [
    "soccer_uefa_champs_league", "soccer_epl", "soccer_spain_la_liga", 
    "soccer_germany_bundesliga", "soccer_italy_serie_a", "soccer_netherlands_eredivisie",
    "basketball_nba", "tennis_atp_dubai"
]

if 'pool' not in st.session_state: st.session_state.pool = []
if 'export_data' not in st.session_state: st.session_state.export_data = []

# --- 2. DE SCANNER (GEFORCEERD) ---
def run_force_scan():
    matches = []
    # We scannen op de markten die je wilde: Winnaar, BTTS en Goals (Over/Under)
    markets = "h2h,btts,totals"
    
    with st.spinner("Grondige scan van alle markten..."):
        for key in LEAGUES:
            url = f"https://api.the-odds-api.com/v4/sports/{key}/odds/"
            params = {'apiKey': API_KEY, 'regions': 'eu', 'markets': markets, 'oddsFormat': 'decimal'}
            try:
                r = requests.get(url, params=params)
                if r.status_code == 200:
                    data = r.json()
                    for game in data:
                        m_time = datetime.fromisoformat(game['commence_time'].replace('Z', '+00:00'))
                        if game.get('bookmakers'):
                            bm = game['bookmakers'][0]
                            for market in bm['markets']:
                                for outcome in market['outcomes']:
                                    price = outcome['price']
                                    # Alleen berekende risico's (1.10 - 1.65)
                                    if 1.10 <= price <= 1.65:
                                        label = ""
                                        if market['key'] == 'h2h': label = f"Win: {outcome['name']}"
                                        elif market['key'] == 'btts': label = f"BTTS: {outcome['name']}"
                                        elif market['key'] == 'totals': label = f"Goals: {outcome['name']} {outcome.get('point','')}"
                                        
                                        matches.append({
                                            "Sport": key.split('_')[1] if '_' in key else key,
                                            "Datum": m_time.strftime("%d-%m-%Y"),
                                            "Tijd": m_time.strftime("%H:%M"),
                                            "Match": f"{game['home_team']} - {game['away_team']}",
                                            "Keuze": label,
                                            "Odd": price
                                        })
            except: continue
    return matches

# --- 3. BEDIENING ---
with st.sidebar:
    st.header("⚙️ Controle")
    if st.button("🚀 1. HAAL WEDSTRIJDEN OP"):
        st.session_state.pool = run_force_scan()
        st.success(f"{len(st.session_state.pool)} kansen geladen!")

    if st.session_state.pool:
        st.divider()
        if st.button("📋 2. MAAK DE 4 BETSLIPS"):
            st.session_state.export_data = []
            targets = [1.5, 2.0, 3.0, 5.0]
            for target in targets:
                # Pak een random sample voor de berekening
                sample = random.sample(st.session_state.pool, min(50, len(st.session_state.pool)))
                best_combo, closest_diff = None, 999
                for r in range(2, 5):
                    for combo in itertools.combinations(sample, r):
                        total = 1.0
                        for m in combo: total *= m['Odd']
                        if target <= total <= (target * 1.3):
                            if abs(total - target) < closest_diff:
                                closest_diff = abs(total - target)
                                best_combo, f_odd = combo, round(total, 2)
                
                if best_combo:
                    for m in best_combo:
                        st.session_state.export_data.append({
                            "Slip_ID": f"Target {target} (@{f_odd})",
                            "Match_Datum": m['Datum'], "Tijd": m['Tijd'],
                            "Wedstrijd": m['Match'], "Keuze": m['Keuze'], 
                            "Odd": m['Odd'], "Status": "OPEN"
                        })
                    # Witregel voor Sheets
                    st.session_state.export_data.append({k: "" for k in ["Slip_ID", "Match_Datum", "Tijd", "Wedstrijd", "Keuze", "Odd", "Status"]})
            st.rerun()

# --- 4. OUTPUT ---
if st.session_state.export_data:
    st.subheader("📑 Professionele Betslips (Onder elkaar)")
    df_export = pd.DataFrame(st.session_state.export_data)
    st.table(df_export)
    
    csv = df_export.to_csv(index=False).encode('utf-8')
    st.download_button("📥 DOWNLOAD VOOR GOOGLE SHEETS", csv, "pro_daily_bets.csv", "text/csv")
    
    if st.button("🗑️ Wis en Opnieuw"):
        st.session_state.export_data = []
        st.rerun()
elif st.session_state.pool:
    st.write("### Beschikbare data voor slips:")
    st.dataframe(pd.DataFrame(st.session_state.pool))
