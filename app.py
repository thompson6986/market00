import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timezone, timedelta
import itertools
import random

# --- 1. CONFIGURATIE ---
st.set_page_config(page_title="Pro Punter - Force Scan", page_icon="⚖️", layout="wide")
API_KEY = 'ae33f20cd78d0b2b015703ded3330fcb'

st.title("⚖️ Pro Punter - Forceer Data")

if 'pool' not in st.session_state: st.session_state.pool = []

# --- 2. DE SCANNER (ZONDER STRENGE FILTERS) ---
def force_scan():
    matches = []
    # De meest actieve leagues van dit moment
    leagues = ["soccer_uefa_champs_league", "soccer_epl", "basketball_nba", "tennis_atp_dubai", "soccer_netherlands_eredivisie"]
    
    with st.spinner("API raadplegen..."):
        for key in leagues:
            url = f"https://api.the-odds-api.com/v4/sports/{key}/odds/"
            params = {'apiKey': API_KEY, 'regions': 'eu', 'markets': 'h2h,totals', 'oddsFormat': 'decimal'}
            try:
                r = requests.get(url, params=params)
                data = r.json()
                
                if r.status_code != 200:
                    st.error(f"API Fout bij {key}: {data.get('message', 'Onbekende fout')}")
                    continue

                for game in data:
                    # We halen het tijdfilter er even HELEMAAL uit om te zien of er data is
                    m_time = datetime.fromisoformat(game['commence_time'].replace('Z', '+00:00'))
                    
                    if game.get('bookmakers'):
                        bm = game['bookmakers'][0]
                        for market in bm['markets']:
                            for outcome in market['outcomes']:
                                price = outcome['price']
                                # Zeer ruime range voor debuggen
                                if 1.05 <= price <= 2.50:
                                    matches.append({
                                        "Sport": key, 
                                        "Tijd": m_time.strftime("%d-%m %H:%M"),
                                        "Match": f"{game['home_team']} - {game['away_team']}",
                                        "Keuze": outcome['name'], 
                                        "Odd": price
                                    })
            except Exception as e:
                st.error(f"Netwerkfout: {e}")
    return matches

# --- 3. UI ---
if st.button("🚀 FORCEER SCAN (LAAT ALLES ZIEN)"):
    st.session_state.pool = force_scan()
    if st.session_state.pool:
        st.success(f"{len(st.session_state.pool)} opties gevonden!")
    else:
        st.error("De API geeft momenteel GEEN data terug voor deze sporten. Controleer of je API-key nog geldig is (vrij verbruik is vaak beperkt).")

if st.session_state.pool:
    df = pd.DataFrame(st.session_state.pool)
    st.dataframe(df)

    # De knop om de betslips te maken
    if st.button("📋 MAAK 4 BETSLIPS (1.5, 2, 3, 5)"):
        # Logica om uit de getoonde tabel de 4 slips te trekken
        export_data = []
        for target in [1.5, 2.0, 3.0, 5.0]:
            # Pak een random setje uit de lijst die we net zagen
            sample = random.sample(st.session_state.pool, min(30, len(st.session_state.pool)))
            # Vind een combo die dicht bij de target ligt
            for r in range(2, 5):
                for combo in itertools.combinations(sample, r):
                    total = 1.0
                    for m in combo: total *= m['Odd']
                    if target <= total <= (target + 0.5):
                        for c in combo:
                            export_data.append({
                                "Slip_ID": f"Target {target} (@{round(total,2)})",
                                "Match": c['Match'], "Keuze": c['Keuze'], "Odd": c['Odd'], "Tijd": c['Tijd']
                            })
                        export_data.append({k: "" for k in ["Slip_ID", "Match", "Keuze", "Odd", "Tijd"]})
                        break
                else: continue
                break
        st.table(pd.DataFrame(export_data))
