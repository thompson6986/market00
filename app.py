import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- CONFIGURATIE ---
st.set_page_config(page_title="Pro Punter Station", page_icon="🏆", layout="wide")

# Jouw nieuwe API Key
API_KEY = 'ae33f20cd78d0b2b015703ded3330fcb'

# Initialiseer archief
if 'archief' not in st.session_state:
    st.session_state.archief = pd.DataFrame(columns=["Tijd", "Slip Doel", "Competitie", "Wedstrijd", "Keuze", "Odd", "Inzet"])

st.title("🏆 Professional Betting Station")
st.markdown(f"**Datum:** Woensdag 25 februari 2026 | **Focus:** Berekende risico's & Value")

# --- SIDEBAR: DATABASE & /CLEAR ---
with st.sidebar:
    st.header("📂 Beheer")
    if not st.session_state.archief.empty:
        open_geld = st.session_state.archief['Inzet'].sum()
        st.write(f"Inzet in open bets: **{open_geld} units**")
        
        # De gevraagde /clear aanpassing
        if st.button(f"🗑️ /clear (Retourneer {open_geld} units)"):
            st.session_state.archief = pd.DataFrame(columns=["Tijd", "Slip Doel", "Competitie", "Wedstrijd", "Keuze", "Odd", "Inzet"])
            st.success("Geld geretourneerd naar open balans.")
            st.rerun()
    else:
        st.info("Geen openstaande weddenschappen.")

# --- SCANNER: LIVE DATA ---
leagues = {
    "Champions League": "soccer_uefa_champs_league",
    "Europa League": "soccer_uefa_europa_league",
    "Premier League": "soccer_epl",
    "Eredivisie": "soccer_netherlands_eredivisie",
    "België Pro League": "soccer_belgium_first_division"
}

st.subheader("🚀 Live Odds Scanner")
selected_league = st.selectbox("Kies competitie:", list(leagues.keys()))

if st.button("HAAL DATA OP"):
    with st.spinner("Odds ophalen..."):
        url = f"https://api.the-odds-api.com/v4/sports/{leagues[selected_league]}/odds/"
        params = {'apiKey': API_KEY, 'regions': 'eu', 'markets': 'h2h,correct_score', 'oddsFormat': 'decimal'}
        
        try:
            r = requests.get(url, params=params)
            if r.status_code == 200:
                data = r.json()
                matches = []
                for game in data:
                    start = datetime.fromisoformat(game['commence_time'].replace('Z', '')).strftime('%d-%m %H:%M')
                    odds = {"0-0": "N/A"}
                    if game['bookmakers']:
                        bm = game['bookmakers'][0] # Pak de hoofdbookmaker
                        for m in bm['markets']:
                            if m['key'] == 'h2h':
                                for o in m['outcomes']: odds[o['name']] = o['price']
                            if m['key'] == 'correct_score':
                                for o in m['outcomes']:
                                    if o['name'] == '0-0': odds["0-0"] = o['price']
                    
                    matches.append({
                        "Tijd": start,
                        "Match": f"{game['home_team']} - {game['away_team']}",
                        "1": odds.get(game['home_team'], "N/A"),
                        "X": odds.get('Draw', "N/A"),
                        "2": odds.get(game['away_team'], "N/A"),
                        "0-0": odds["0-0"]
                    })
                st.session_state.temp_odds = pd.DataFrame(matches)
            else:
                st.error("API Error. Controleer sleutel.")
        except:
            st.error("Fout bij verbinden.")

# --- SELECTIE VOOR BETSLIPS ---
if 'temp_odds' in st.session_state:
    st.divider()
    df = st.session_state.temp_odds
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.subheader("🎯 Voeg toe aan je Dagelijkse Slips")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        m = st.selectbox("Match:", df['Match'])
    with c2:
        row = df[df['Match'] == m].iloc[0]
        keuze = st.selectbox("Markt:", ["1", "X", "2", "0-0"])
        gekozen_odd = row[keuze]
    with c3:
        doel = st.selectbox("Voor Slip:", [1.5, 2.0, 3.0, 5.0])
    with c4:
        if st.button("ZET OP SLIP"):
            # Professionele punter regel: minimaal 1 unit inzet
            new_bet = {
                "Tijd": row['Tijd'],
                "Slip Doel": f"Odd {doel}",
                "Competitie": selected_league,
                "Wedstrijd": m,
                "Keuze": keuze,
                "Odd": gekozen_odd,
                "Inzet": 1.0
            }
            st.session_state.archief = pd.concat([st.session_state.archief, pd.DataFrame([new_bet])], ignore_index=True)
            st.toast(f"Match toegevoegd aan de {doel} slip.")

# --- HET ARCHIEF ---
st.divider()
st.subheader("📋 Jouw Betslips van Vandaag")
if not st.session_state.archief.empty:
    st.table(st.session_state.archief)
    csv = st.session_state.archief.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download voor administratie", csv, "betslips_vandaag.csv", "text/csv")
else:
    st.info("Nog geen wedstrijden geselecteerd voor de slips van vandaag.")
