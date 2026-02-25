import streamlit as st
import pandas as pd
import requests
import re
from datetime import datetime

# --- CONFIGURATIE ---
st.set_page_config(page_title="Pro Punter Station", page_icon="🏆", layout="wide")

# Jouw API Key (controleer op spaties!)
API_KEY = 'ae33f20cd78d0b2b015703ded3330fcb'

if 'archief' not in st.session_state:
    st.session_state.archief = pd.DataFrame(columns=["Tijd", "Slip Doel", "Competitie", "Wedstrijd", "Keuze", "Odd", "Inzet"])

st.title("🏆 Professional Betting Station")
st.markdown(f"**Datum:** Woensdag 25 februari 2026")

# --- SIDEBAR: BEHEER ---
with st.sidebar:
    st.header("📂 Beheer")
    if not st.session_state.archief.empty:
        open_geld = st.session_state.archief['Inzet'].sum()
        st.write(f"Inzet in open bets: **{open_geld} units**")
        if st.button(f"🗑️ /clear (Retourneer {open_geld})"):
            st.session_state.archief = pd.DataFrame(columns=["Tijd", "Slip Doel", "Competitie", "Wedstrijd", "Keuze", "Odd", "Inzet"])
            st.rerun()

# --- MODUS KEUZE ---
tab1, tab2 = st.tabs(["🚀 Automatische API Scan", "📋 OddsPortal Handmatige Scan"])

with tab1:
    st.subheader("API Scanner")
    league_key = st.selectbox("Selecteer League:", ["soccer_uefa_champs_league", "soccer_epl", "soccer_netherlands_eredivisie"], key="api_l")
    if st.button("Scan via API"):
        url = f"https://api.the-odds-api.com/v4/sports/{league_key}/odds/?apiKey={API_KEY}&regions=eu&markets=h2h,correct_score"
        r = requests.get(url)
        if r.status_code == 200:
            data = r.json()
            # ... (Rest van de API verwerking zoals voorheen)
            st.success("Data opgehaald!")
        else:
            st.error(f"Foutmelding van API: {r.status_code}. Dit betekent meestal dat de sleutel nog niet actief is of de limiet bereikt is.")

with tab2:
    st.subheader("Back-up: OddsPortal Plakken")
    manual_data = st.text_area("Plak hier de odds (als de API niet werkt):", height=200)
    if st.button("Analyseer Plakwerk"):
        # Super-regex om odds en wedstrijden uit rommelige tekst te vissen
        lines = manual_data.split('\n')
        found = []
        for i, line in enumerate(lines):
            if " - " in line and ":" not in line: # Wedstrijdnaam
                for j in range(i, i+10): # Zoek odds in de buurt
                    if j < len(lines) and re.search(r'\d+\.\d{2}', lines[j]):
                        odd = re.findall(r'\d+\.\d{2}', lines[j])[0]
                        found.append({"Tijd": "Vandaag", "Match": line, "Odd": odd})
                        break
        if found:
            st.session_state.temp_odds = pd.DataFrame(found)
            st.table(st.session_state.temp_odds)
        else:
            st.warning("Geen herkenbare data gevonden. Probeer de hele tabel te kopiëren.")

# --- OPSLAAN LOGICA ---
if 'temp_odds' in st.session_state:
    st.divider()
    # (Zelfde selectie-boxen als voorheen om de 1.5, 2, 3 en 5 slips te vullen)
    st.info("Selecteer hierboven je wedstrijd en voeg hem toe aan je archief.")
