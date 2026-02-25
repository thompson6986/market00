import streamlit as st
import pandas as pd
import re
from datetime import datetime
import requests

st.set_page_config(page_title="Pro Global Betting Station", page_icon="⚽", layout="wide")

API_KEY = '5890cd7c7251e5b9fe336d224e2b6bb4'

# Initialiseer archief
if 'archief' not in st.session_state:
    st.session_state.archief = pd.DataFrame(columns=["Tijdstip", "Competitie", "Wedstrijd", "Odd", "Inzet", "Pot. Winst"])

st.title("⚽ Professional Global Betting Station")

# --- SIDEBAR: DATA BEHEER ---
with st.sidebar:
    st.header("📂 Data Beheer")
    uploaded_file = st.file_uploader("Upload CSV Archief", type="csv")
    if uploaded_file and st.button("Importeer Data"):
        uploaded_df = pd.read_csv(uploaded_file)
        st.session_state.archief = pd.concat([st.session_state.archief, uploaded_df], ignore_index=True).drop_duplicates()
        st.success("Data geladen!")
    
    st.divider()
    # De gevraagde /clear functionaliteit: 
    # In een archief-context tonen we wat er 'vrijkomt' bij het wissen
    if not st.session_state.archief.empty:
        total_back = st.session_state.archief['Inzet'].sum()
        if st.button(f"🗑️ CLEAR ARCHIEF (Retour: {total_back} units)"):
            st.session_state.archief = pd.DataFrame(columns=["Tijdstip", "Competitie", "Wedstrijd", "Odd", "Inzet", "Pot. Winst"])
            st.success(f"Archief gewist. {total_back} units vrijgegeven.")
            st.rerun()

# --- HOOFDSCHERM: KIES MODUS ---
tab1, tab2 = st.tabs(["🚀 Automatische API Scan", "📋 OddsPortal Handmatige Scan"])

# --- TAB 1: AUTOMATISCH (Uitgebreide Lijst) ---
with tab1:
    st.subheader("Wereldwijde Competitie Scan")
    
    # Uitgebreide lijst met competities
    leagues = {
        "--- EUROPA ---": "",
        "Eredivisie (NL)": "soccer_netherlands_eredivisie",
        "Premier League (UK)": "soccer_epl",
        "Championship (UK)": "soccer_efl_champ",
        "Bundesliga (DE)": "soccer_germany_bundesliga",
        "Serie A (IT)": "soccer_italy_serie_a",
        "La Liga (ES)": "soccer_spain_la_liga",
        "Ligue 1 (FR)": "soccer_france_ligue_one",
        "Primeira Liga (PT)": "soccer_portugal_primeira_liga",
        "België Pro League (BE)": "soccer_belgium_first_division",
        "--- AZIË & OVERIG ---": "",
        "J-League (JP)": "soccer_japan_j_league",
        "K-League (KR)": "soccer_south_korea_k_league_1",
        "A-League (AU)": "soccer_australia_aleague",
        "MLS (USA)": "soccer_usa_mls",
        "Copa Libertadores": "soccer_conmebol_copa_libertadores"
    }
    
    selected_name = st.selectbox("Kies competitie:", list(leagues.keys()))
    selected_key = leagues[selected_name]
    
    if st.button("START API SCAN") and selected_key != "":
        with st.spinner(f'Scannen van {selected_name}...'):
            url = f"https://api.the-odds-api.com/v4/sports/{selected_key}/odds/"
            params = {'apiKey': API_KEY, 'regions': 'eu', 'markets': 'correct_score'}
            r = requests.get(url, params=params)
            
            if r.status_code == 200:
                data = r.json()
                api_results = []
                for game in data:
                    odd_00 = None
                    if 'bookmakers' in game and game['bookmakers']:
                        for m in game['bookmakers'][0]['markets']:
                            if m['key'] == 'correct_score':
                                for o in m['outcomes']:
                                    if o['name'] == '0-0': odd_00 = o['price']
                    if odd_00:
                        api_results.append({
                            "Wedstrijd": f"{game['home_team']} - {game['away_team']}",
                            "Odd": odd_00,
                            "Competitie": selected_name
                        })
                if api_results:
                    st.session_state.last_scan = pd.DataFrame(api_results)
                    st.table(st.session_state.last_scan)
                else:
                    st.warning("Geen 0-0 odds gevonden voor deze competitie.")
            else:
                st.error("API kon data niet ophalen.")

# --- TAB 2: HANDMATIG (Voor Thailand en overige) ---
with tab2:
    st.subheader("OddsPortal Scraper")
    manual_comp = st.text_input("Naam van competitie:", "Thai League 1")
    input_data = st.text_area("Plak hier de data van OddsPortal:", height=150, key="manual_input")
    
    if st.button('ANALYSEER PLAKWERK'):
        if input_data:
            lines = [l.strip() for l in input_data.split('\n') if l.strip()]
            manual_results = []
            for i, line in enumerate(lines):
                if "0:0" in line or "0-0" in line:
                    area = " ".join(lines[i:i+4])
                    odds = re.findall(r'\b\d{1,2}\.\d{2}\b', area)
                    if odds:
                        match_name = "Onbekend"
                        for j in range(i, max(-1, i-10), -1):
                            if " - " in lines[j] and ":" not in lines[j]:
                                match_name = lines[j]; break
                        manual_results.append({
                            "Wedstrijd": match_name, 
                            "Odd": max([float(o) for o in odds]), 
                            "Competitie": manual_comp
                        })
            if manual_results:
                st.session_state.last_scan = pd.DataFrame(manual_results)
                st.table(st.session_state.last_scan)
            else:
                st.error("Geen data herkend.")

# --- OPSLAAN SECTIE ---
if 'last_scan' in st.session_state:
    st.divider()
    col_a, col_b = st.columns(2)
    with col_a:
        selected_match = st.selectbox("Selecteer match om op te slaan:", st.session_state.last_scan['Wedstrijd'])
    with col_b:
        # Inzet volgens jouw regel: minimaal 1
        inzet = st.number_input("Inzet (units):", min_value=1.0, value=1.0, step=1.0)
        if st.button("VOEG TOE AAN ARCHIEF"):
            m_info = st.session_state.last_scan[st.session_state.last_scan['Wedstrijd'] == selected_match].iloc[0]
            nieuwe_rij = {
                "Tijdstip": datetime.now().strftime("%d-%m %H:%M"),
                "Competitie": m_info['Competitie'],
                "Wedstrijd": selected_match,
                "Odd": m_info['Odd'],
                "Inzet": inzet,
                "Pot. Winst": round(m_info['Odd'] * inzet, 2)
            }
            st.session_state.archief = pd.concat([st.session_state.archief, pd.DataFrame([nieuwe_rij])], ignore_index=True)
            st.toast(f"Opgeslagen: {selected_match}")

# --- ARCHIEF ---
st.divider()
st.subheader("📊 Dagoverzicht & Archief")
if not st.session_state.archief.empty:
    st.dataframe(st.session_state.archief, use_container_width=True, hide_index=True)
    
    # Statistieken
    totaal_inzet = st.session_state.archief['Inzet'].sum()
    st.write(f"**Totaal risico:** {totaal_inzet} units")
    
    csv = st.session_state.archief.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Archief (CSV)", csv, f"bets_{datetime.now().strftime('%d-%m')}.csv", "text/csv")
