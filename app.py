import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# Pagina instellingen
st.set_page_config(page_title="CL Pro Punter Station", page_icon="🏆", layout="wide")

# CONFIGURATIE
API_KEY = 'Jae33f20cd78d0b2b015703ded3330fcb' # Plak hier je nieuwe key
TARGET_ODDS = [1.5, 2.0, 3.0, 5.0]

if 'archief' not in st.session_state:
    st.session_state.archief = pd.DataFrame(columns=["Tijd", "Slip", "Competitie", "Wedstrijd", "Markt", "Odd", "Inzet"])

st.title("🏆 Champions League & Pro League Station")
st.info(f"Vandaag: Woensdag 25 februari 2026. Tijd voor je 4 berekende slips.")

# --- SIDEBAR: DATABASE BEHEER ---
with st.sidebar:
    st.header("📂 Logboek Beheer")
    if not st.session_state.archief.empty:
        total_staked = st.session_state.archief['Inzet'].sum()
        if st.button(f"🗑️ CLEAR (Retour: {total_staked} units)"):
            st.session_state.archief = pd.DataFrame(columns=["Tijd", "Slip", "Competitie", "Wedstrijd", "Markt", "Odd", "Inzet"])
            st.rerun()

# --- SCANNER ---
leagues = {
    "Champions League": "soccer_uefa_champs_league",
    "Europa League": "soccer_uefa_europa_league",
    "Premier League": "soccer_epl",
    "Eredivisie": "soccer_netherlands_eredivisie"
}

selected_league = st.selectbox("Kies competitie voor scan:", list(leagues.keys()))

if st.button("HAAL LIVE ODDS OP"):
    # We scannen H2H (Winst) en Correct Score (0-0)
    url = f"https://api.the-odds-api.com/v4/sports/{leagues[selected_league]}/odds/"
    params = {'apiKey': API_KEY, 'regions': 'eu', 'markets': 'h2h,correct_score', 'oddsFormat': 'decimal'}
    
    try:
        r = requests.get(url, params=params)
        if r.status_code == 200:
            data = r.json()
            results = []
            for game in data:
                time = datetime.fromisoformat(game['commence_time'].replace('Z', '')).strftime('%d-%m %H:%M')
                
                # Odds extractie
                odds_dict = {"0-0": "N/A"}
                if game['bookmakers']:
                    bm = game['bookmakers'][0] # Pak de eerste grote bookmaker (vaak Pinnacle/Unibet)
                    for m in bm['markets']:
                        if m['key'] == 'h2h':
                            for o in m['outcomes']: odds_dict[o['name']] = o['price']
                        if m['key'] == 'correct_score':
                            for o in m['outcomes']:
                                if o['name'] == '0-0': odds_dict["0-0"] = o['price']
                
                results.append({
                    "Tijd": time,
                    "Match": f"{game['home_team']} - {game['away_team']}",
                    "Home": odds_dict.get(game['home_team'], "N/A"),
                    "Draw": odds_dict.get('Draw', "N/A"),
                    "Away": odds_dict.get(game['away_team'], "N/A"),
                    "CS 0-0": odds_dict["0-0"]
                })
            
            st.session_state.temp_odds = pd.DataFrame(results)
            st.success(f"Scan voltooid. {len(results)} wedstrijden gevonden.")
        else:
            st.error("Check je API Key. Limiet bereikt.")
    except:
        st.error("Verbindingsfout.")

# --- SLIP SELECTIE ---
if 'temp_odds' in st.session_state:
    st.divider()
    st.subheader("🎯 Match Odds aan je Slips")
    df = st.session_state.temp_odds
    st.dataframe(df, use_container_width=True, hide_index=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        match = st.selectbox("Selecteer match:", df['Match'])
    with col2:
        # Hier kun je de specifieke odd kiezen uit de scan
        row = df[df['Match'] == match].iloc[0]
        opties = [row['Home'], row['Draw'], row['Away'], row['CS 0-0']]
        odd_choice = st.selectbox("Kies de Odd:", [o for o in opties if o != "N/A"])
    with col3:
        slip_type = st.selectbox("Voor slip:", TARGET_ODDS)
    with col4:
        if st.button("VOEG TOE"):
            new_entry = {
                "Tijd": row['Tijd'],
                "Slip": f"Odd {slip_type}",
                "Competitie": selected_league,
                "Wedstrijd": match,
                "Markt": "H2H/CS",
                "Odd": odd_choice,
                "Inzet": 1.0
            }
            st.session_state.archief = pd.concat([st.session_state.archief, pd.DataFrame([new_entry])], ignore_index=True)
            st.toast(f"Match toegevoegd aan {slip_type} slip!")

# --- HET LOGBOEK ---
st.divider()
st.subheader("📋 Jouw Betslips voor Vandaag")
if not st.session_state.archief.empty:
    st.table(st.session_state.archief)
    
    # Download voor je eigen administratie
    csv = st.session_state.archief.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Slips (CSV)", csv, f"slips_{datetime.now().strftime('%d-%m')}.csv", "text/csv")
else:
    st.info("Scan een competitie en voeg je eerste berekende weddenschap toe.")
