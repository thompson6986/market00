import streamlit as st
import pandas as pd
import requests
import re
from datetime import datetime

# --- CONFIGURATIE ---
st.set_page_config(page_title="Pro Punter Station v3", page_icon="🏆", layout="wide")

# Jouw API Key
API_KEY = 'ae33f20cd78d0b2b015703ded3330fcb'

# Initialiseer archief in sessie
if 'archief' not in st.session_state:
    st.session_state.archief = pd.DataFrame(columns=["Tijd", "Slip Doel", "Competitie", "Wedstrijd", "Keuze", "Odd", "Inzet"])

st.title("🏆 Professional Global Betting Station")
st.markdown(f"**Datum:** Woensdag 25 februari 2026 | **Status:** Live Market Access")

# --- SIDEBAR: DATABASE & /CLEAR ---
with st.sidebar:
    st.header("📂 Bankroll Beheer")
    if not st.session_state.archief.empty:
        total_staked = st.session_state.archief['Inzet'].sum()
        st.metric("Openstaand Kapitaal", f"{total_staked} units")
        
        # De /clear functie die geld retourneert
        if st.button(f"🗑️ /clear (Retour: {total_staked} units)"):
            st.session_state.archief = pd.DataFrame(columns=["Tijd", "Slip Doel", "Competitie", "Wedstrijd", "Keuze", "Odd", "Inzet"])
            st.success("Lijst gewist. Inzet geretourneerd.")
            st.rerun()
    else:
        st.info("Geen open bets.")
    
    st.divider()
    st.write("Target Slips vandaag: **1.5, 2.0, 3.0, 5.0**")

# --- HOOFDSCHERM: SCANNER ---
tab1, tab2 = st.tabs(["🚀 API Scan (CL & Grote Leagues)", "📋 OddsPortal Scan (Thai & Back-up)"])

# --- TAB 1: API LOGICA ---
with tab1:
    leagues = {
        "Champions League": "soccer_uefa_champs_league",
        "Europa League": "soccer_uefa_europa_league",
        "Premier League (UK)": "soccer_epl",
        "Eredivisie (NL)": "soccer_netherlands_eredivisie",
        "Pro League (BE)": "soccer_belgium_first_division"
    }
    sel_league = st.selectbox("Kies competitie:", list(leagues.keys()))
    
    if st.button("START LIVE API SCAN"):
        # We vragen eerst h2h op (meest stabiel tegen 422 errors)
        url = f"https://api.the-odds-api.com/v4/sports/{leagues[sel_league]}/odds/"
        params = {'apiKey': API_KEY, 'regions': 'eu', 'markets': 'h2h,correct_score', 'oddsFormat': 'decimal'}
        
        with st.spinner("Marktgegevens ophalen..."):
            r = requests.get(url, params=params)
            if r.status_code == 200:
                data = r.json()
                results = []
                for game in data:
                    tijd = datetime.fromisoformat(game['commence_time'].replace('Z', '')).strftime('%d-%m %H:%M')
                    odds_found = {"0-0": "N/A"}
                    if game['bookmakers']:
                        bm = game['bookmakers'][0]
                        for m in bm['markets']:
                            if m['key'] == 'h2h':
                                for o in m['outcomes']: odds_found[o['name']] = o['price']
                            if m['key'] == 'correct_score':
                                for o in m['outcomes']:
                                    if o['name'] == '0-0': odds_found["0-0"] = o['price']
                    
                    results.append({
                        "Tijd": tijd,
                        "Match": f"{game['home_team']} - {game['away_team']}",
                        "1": odds_found.get(game['home_team'], "N/A"),
                        "X": odds_found.get('Draw', "N/A"),
                        "2": odds_found.get(game['away_team'], "N/A"),
                        "0-0": odds_found["0-0"],
                        "Comp": sel_league
                    })
                st.session_state.current_scan = pd.DataFrame(results)
                st.success("API Data succesvol geladen.")
            else:
                st.error(f"API Error {r.status_code}. Probeer Tab 2 (OddsPortal) voor deze competitie.")

# --- TAB 2: ODDSPORTAL LOGICA ---
with tab2:
    st.subheader("Handmatige Scraper")
    manual_comp = st.text_input("Competitie Naam:", "Thai League 1")
    plak_data = st.text_area("Plak hier de tekst van OddsPortal:", height=150)
    
    if st.button("ANALYSEER PLAKWERK"):
        lines = [l.strip() for l in plak_data.split('\n') if l.strip()]
        manual_results = []
        for i, line in enumerate(lines):
            # Zoek patronen voor scores en wedstrijden
            if "0:0" in line or "0-0" in line or " - " in line:
                odds = re.findall(r'\b\d{1,2}\.\d{2}\b', " ".join(lines[i:i+6]))
                if odds:
                    match_name = line if " - " in line else "Match in buurt van 0-0"
                    manual_results.append({
                        "Tijd": datetime.now().strftime("%d-%m %H:%M"),
                        "Match": match_name,
                        "0-0": max([float(o) for o in odds]),
                        "Comp": manual_comp,
                        "1": "N/A", "X": "N/A", "2": "N/A"
                    })
        if manual_results:
            st.session_state.current_scan = pd.DataFrame(manual_results).drop_duplicates(subset=['Match'])
            st.table(st.session_state.current_scan)

# --- SELECTIE EN OPSLAAN ---
if 'current_scan' in st.session_state:
    st.divider()
    st.subheader("🎯 Match toevoegen aan je 4 Betslips")
    df = st.session_state.current_scan
    st.dataframe(df, use_container_width=True, hide_index=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        sel_m = st.selectbox("Kies Wedstrijd:", df['Match'])
    with c2:
        row = df[df['Match'] == sel_m].iloc[0]
        # Toon alleen beschikbare odds
        opties = {k: v for k, v in row.items() if k in ["1", "X", "2", "0-0"] and v != "N/A"}
        keuze = st.selectbox("Kies je Bet:", list(opties.keys()))
        odd_val = opties[keuze]
    with c3:
        doel = st.selectbox("Voor Slip (Odd Doel):", [1.5, 2.0, 3.0, 5.0])
    with c4:
        if st.button("VOEG TOE AAN SLIP"):
            new_bet = {
                "Tijd": row['Tijd'],
                "Slip Doel": f"Slip {doel}",
                "Competitie": row['Comp'],
                "Wedstrijd": sel_m,
                "Keuze": keuze,
                "Odd": odd_val,
                "Inzet": 1.0
            }
            st.session_state.archief = pd.concat([st.session_state.archief, pd.DataFrame([new_bet])], ignore_index=True)
            st.toast(f"Match opgeslagen voor slip {doel}")

# --- ARCHIEF ---
st.divider()
st.subheader("📋 Jouw Betting Logboek (Betslips)")
if not st.session_state.archief.empty:
    st.table(st.session_state.archief)
    csv = st.session_state.archief.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Archief (CSV)", csv, f"mijn_bets_{datetime.now().strftime('%d-%m')}.csv", "text/csv")
else:
    st.info("Scan een league en selecteer je wedstrijden voor vandaag.")
