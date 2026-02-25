import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timezone, timedelta
import itertools
import random

# --- 1. CONFIGURATIE ---
st.set_page_config(page_title="Pro Punter Debug Edition", page_icon="🚨", layout="wide")
API_KEY = 'ae33f20cd78d0b2b015703ded3330fcb'

st.title("🚨 Pro Punter - Forceer Scan Mode")
st.caption("Deze versie negeert tijdfilters om te achterhalen waarom er 0 resultaten zijn.")

# We focussen op de meest betrouwbare leagues om resultaten te garanderen
LEAGUES_TO_SCAN = [
    "soccer_uefa_champs_league", "soccer_epl", "soccer_spain_la_liga", 
    "soccer_italy_serie_a", "soccer_germany_bundesliga", "basketball_nba"
]

if 'pool' not in st.session_state: st.session_state.pool = []
if 'export_data' not in st.session_state: st.session_state.export_data = []

def force_scan():
    matches = []
    # Test op H2H (meest stabiele markt)
    markets = "h2h" 
    
    with st.spinner("Systeem dwingen om data op te halen..."):
        for key in LEAGUES_TO_SCAN:
            url = f"https://api.the-odds-api.com/v4/sports/{key}/odds/"
            params = {'apiKey': API_KEY, 'regions': 'eu', 'markets': markets, 'oddsFormat': 'decimal'}
            try:
                r = requests.get(url, params=params)
                # DEBUG: Laat statuscode zien als het misgaat
                if r.status_code != 200:
                    st.error(f"Fout bij {key}: Status {r.status_code}")
                    continue
                
                data = r.json()
                if not data:
                    continue
                
                for game in data:
                    # WE HALEN DE DATUM CHECK ER NU UIT OM RESULTATEN TE FORCEREN
                    match_time = datetime.fromisoformat(game['commence_time'].replace('Z', '+00:00'))
                    
                    if game.get('bookmakers'):
                        bm = game['bookmakers'][0]
                        for market in bm['markets']:
                            for outcome in market['outcomes']:
                                price = outcome['price']
                                
                                # Ruime range voor debuggen
                                if 1.05 <= price <= 2.00:
                                    matches.append({
                                        "Sport": key,
                                        "Datum": match_time.strftime("%d-%m-%Y"),
                                        "Tijd": match_time.strftime("%H:%M"),
                                        "Match": f"{game['home_team']} - {game['away_team']}",
                                        "Keuze": outcome['name'],
                                        "Odd": price
                                    })
            except Exception as e:
                st.warning(f"Error bij {key}: {str(e)}")
                continue 
    return matches

# --- UI ---
with st.sidebar:
    if st.button("🚀 FORCEER SCAN NU"):
        st.session_state.pool = force_scan()
        if st.session_state.pool:
            st.success(f"SUCCES! {len(st.session_state.pool)} kansen gevonden!")
        else:
            st.error("Nog steeds 0. Dit betekent dat de API-sleutel mogelijk verlopen is of het limiet heeft bereikt.")

if st.session_state.pool:
    st.write("### Gevonden Wedstrijden (Ruwe Data)")
    st.dataframe(pd.DataFrame(st.session_state.pool))
    
    # Knoppen voor je slips
    if st.button("📋 MAAK SLIPS VAN DEZE DATA"):
        # Hieronder de logica voor de 4 slips (1.5, 2, 3, 5)
        for target in [1.5, 2.0, 3.0, 5.0]:
            pool_sample = random.sample(st.session_state.pool, min(50, len(st.session_state.pool)))
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
                        "Wedstrijd": m['Match'], "Keuze": m['Keuze'], "Odd": m['Odd'], "Status": "OPEN"
                    })
        st.rerun()

if st.session_state.export_data:
    st.table(pd.DataFrame(st.session_state.export_data))
    csv = pd.DataFrame(st.session_state.export_data).to_csv(index=False).encode('utf-8')
    st.download_button("📥 DOWNLOAD CSV", csv, "pro_bets.csv", "text/csv")
