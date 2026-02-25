import streamlit as st
import pandas as pd
import requests
import re
from datetime import datetime

# --- 1. CONFIGURATIE (MOET BOVENAAN) ---
st.set_page_config(page_title="Pro Punter Station", page_icon="🏆", layout="wide")

# Jouw API Key
API_KEY = 'ae33f20cd78d0b2b015703ded3330fcb'

# Initialiseer sessie variabelen
if 'archief' not in st.session_state:
    st.session_state.archief = pd.DataFrame(columns=["Tijd", "Slip Doel", "Competitie", "Wedstrijd", "Keuze", "Odd", "Inzet"])

if 'current_scan' not in st.session_state:
    st.session_state.current_scan = pd.DataFrame()

st.title("🏆 Professional Betting Station")
st.markdown(f"**Datum:** Woensdag 25 februari 2026")

# --- 2. SIDEBAR: BEHEER & /CLEAR ---
with st.sidebar:
    st.header("📂 Beheer")
    if not st.session_state.archief.empty:
        open_geld = st.session_state.archief['Inzet'].sum()
        st.metric("Geld in open bets", f"{open_geld} units")
        if st.button(f"🗑️ /clear (Retourneer {open_geld} units)"):
            st.session_state.archief = pd.DataFrame(columns=["Tijd", "Slip Doel", "Competitie", "Wedstrijd", "Keuze", "Odd", "Inzet"])
            st.rerun()
    st.divider()
    st.write("Doelen: **1.5 | 2.0 | 3.0 | 5.0**")

# --- 3. SCANNER MODUS ---
tab1, tab2 = st.tabs(["🚀 API Scan", "📋 OddsPortal (Handmatig & Naam aanpassen)"])

with tab1:
    st.subheader("API Scanner")
    league_key = st.selectbox("Kies League:", ["soccer_uefa_champs_league", "soccer_epl", "soccer_netherlands_eredivisie", "soccer_belgium_first_division"])
    if st.button("Scan via API"):
        url = f"https://api.the-odds-api.com/v4/sports/{league_key}/odds/?apiKey={API_KEY}&regions=eu&markets=h2h,correct_score"
        r = requests.get(url)
        if r.status_code == 200:
            data = r.json()
            api_results = []
            for game in data:
                tijd = datetime.fromisoformat(game['commence_time'].replace('Z', '')).strftime('%d-%m %H:%M')
                odds = {"0-0": "N/A"}
                if game['bookmakers']:
                    bm = game['bookmakers'][0]
                    for m in bm['markets']:
                        if m['key'] == 'h2h':
                            for o in m['outcomes']: odds[o['name']] = o['price']
                        if m['key'] == 'correct_score':
                            for o in m['outcomes']:
                                if o['name'] == '0-0': odds["0-0"] = o['price']
                api_results.append({"Tijd": tijd, "Match": f"{game['home_team']} - {game['away_team']}", "1": odds.get(game['home_team'], "N/A"), "X": odds.get('Draw', "N/A"), "2": odds.get(game['away_team'], "N/A"), "0-0": odds["0-0"], "Comp": league_key})
            st.session_state.current_scan = pd.DataFrame(api_results)
        else:
            st.error(f"API Error {r.status_code}")

with tab2:
    st.subheader("OddsPortal Scraper")
    manual_comp = st.text_input("Competitie:", "Champions League")
    plak_data = st.text_area("Plak hier de tekst van de website:", height=150)
    if st.button("Analyseer Tekst"):
        found_odds = re.findall(r'\b\d{1,2}\.\d{2}\b', plak_data)
        if found_odds:
            # We maken een tijdelijke rij aan met de gevonden hoogste odd
            st.session_state.current_scan = pd.DataFrame([{
                "Tijd": datetime.now().strftime("%d-%m %H:%M"),
                "Match": "Geef hieronder een naam...", 
                "0-0": max([float(o) for o in found_odds]),
                "Comp": manual_comp,
                "1": "N/A", "X": "N/A", "2": "N/A"
            }])
        else:
            st.error("Geen odds gevonden in de tekst.")

# --- 4. NAAMGEVING & OPSLAAN (HET GEDEELTE DAT NIET LUKTE) ---
if not st.session_state.current_scan.empty:
    st.divider()
    st.subheader("🎯 Wedstrijd een naam geven & Opslaan")
    
    df = st.session_state.current_scan
    # We laten de gebruiker de wedstrijdnaam overschrijven
    with st.container():
        c1, c2 = st.columns(2)
        with c1:
            nieuwe_naam = st.text_input("Wat is de naam van de wedstrijd?", value=df.iloc[0]['Match'])
            gekozen_tijd = st.text_input("Tijdstip (bijv. 21:00):", value=df.iloc[0]['Tijd'])
        with c2:
            gekozen_odd = st.number_input("Bevestig de Odd:", value=float(df.iloc[0]['0-0']) if df.iloc[0]['0-0'] != "N/A" else 1.00)
            slip_doel = st.selectbox("Voor welke slip?", [1.5, 2.0, 3.0, 5.0])

        if st.button("VOEG TOE AAN ARCHIEF"):
            nieuwe_bet = {
                "Tijd": gekozen_tijd,
                "Slip Doel": f"Slip {slip_doel}",
                "Competitie": df.iloc[0]['Comp'],
                "Wedstrijd": nieuwe_naam,
                "Keuze": "0-0",
                "Odd": gekozen_odd,
                "Inzet": 1.0
            }
            st.session_state.archief = pd.concat([st.session_state.archief, pd.DataFrame([nieuwe_bet])], ignore_index=True)
            st.success(f"Opgeslagen: {nieuwe_naam} voor slip {slip_doel}")

# --- 5. HET ARCHIEF ---
st.divider()
st.subheader("📊 Je Betslips voor Vandaag")
st.table(st.session_state.archief)
