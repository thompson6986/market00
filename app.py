import streamlit as st
import pandas as pd
import re
from datetime import datetime
import requests

# Configuuratie van de pagina
st.set_page_config(page_title="Pro Global Betting Station", page_icon="⚽", layout="wide")

# API Key van de gebruiker
API_KEY = '5890cd7c7251e5b9fe336d224e2b6bb4'

# 1. Initialiseer het archief (Database)
if 'archief' not in st.session_state:
    st.session_state.archief = pd.DataFrame(columns=["Tijdstip", "Competitie", "Wedstrijd", "Odd", "Inzet", "Pot. Winst"])

st.title("⚽ Professional Global Betting Station")
st.caption(f"Datum: {datetime.now().strftime('%d-%m-%Y')} | Beheer je berekende weddenschappen")

# --- SIDEBAR: DATA BEHEER & /CLEAR FUNCTIE ---
with st.sidebar:
    st.header("📂 Data Beheer")
    
    # Upload functie
    uploaded_file = st.file_uploader("Upload CSV Archief", type="csv")
    if uploaded_file and st.button("Importeer Data"):
        uploaded_df = pd.read_csv(uploaded_file)
        st.session_state.archief = pd.concat([st.session_state.archief, uploaded_df], ignore_index=True).drop_duplicates()
        st.success("Data geladen!")
    
    st.divider()
    
    # De /clear functionaliteit: Geeft inzet van open bets terug
    if not st.session_state.archief.empty:
        total_back = st.session_state.archief['Inzet'].sum()
        st.write(f"Openstaand kapitaal: **{total_back} units**")
        if st.button(f"🗑️ CLEAR ARCHIEF (Retour: {total_back})"):
            st.session_state.archief = pd.DataFrame(columns=["Tijdstip", "Competitie", "Wedstrijd", "Odd", "Inzet", "Pot. Winst"])
            st.success(f"Archief gewist. {total_back} units geretourneerd naar bankroll.")
            st.rerun()

# --- HOOFDSCHERM: SCANNER MODI ---
tab1, tab2 = st.tabs(["🚀 Automatische API Scan (CL, Europa, etc.)", "📋 OddsPortal Handmatige Scan (Thailand)"])

# --- TAB 1: AUTOMATISCH (Inclusief Champions League) ---
with tab1:
    st.subheader("Wereldwijde Competitie Scan")
    
    leagues = {
        "--- INTERNATIONAAL ---": "",
        "Champions League (EU)": "soccer_uefa_champs_league",
        "Europa League (EU)": "soccer_uefa_europa_league",
        "Europa Conference League": "soccer_uefa_europa_conference_league",
        "Nations League (EU)": "soccer_uefa_nations_league",
        "--- EUROPA ---": "",
        "Eredivisie (NL)": "soccer_netherlands_eredivisie",
        "België Pro League (BE)": "soccer_belgium_first_division",
        "Premier League (UK)": "soccer_epl",
        "Championship (UK)": "soccer_efl_champ",
        "Bundesliga (DE)": "soccer_germany_bundesliga",
        "Serie A (IT)": "soccer_italy_serie_a",
        "La Liga (ES)": "soccer_spain_la_liga",
        "Ligue 1 (FR)": "soccer_france_ligue_one",
        "--- AZIË & OVERIG ---": "",
        "J-League (JP)": "soccer_japan_j_league",
        "K-League (KR)": "soccer_south_korea_k_league_1",
        "A-League (AU)": "soccer_australia_aleague",
        "MLS (USA)": "soccer_usa_mls",
        "Copa Libertadores": "soccer_conmebol_copa_libertadores"
    }
    
    selected_name = st.selectbox("Kies competitie voor automatische scan:", list(leagues.keys()))
    selected_key = leagues[selected_name]
    
    if st.button("START API SCAN") and selected_key != "":
        with st.spinner(f'Data ophalen voor {selected_name}...'):
            url = f"https://api.the-odds-api.com/v4/sports/{selected_key}/odds/"
            params = {'apiKey': API_KEY, 'regions': 'eu', 'markets': 'correct_score'}
            try:
                r = requests.get(url, params=params)
                if r.status_code == 200:
                    data = r.json()
                    api_results = []
                    for game in data:
                        odd_00 = None
                        game_time = datetime.fromisoformat(game['commence_time'].replace('Z', '')).strftime('%d-%m %H:%M')
                        if 'bookmakers' in game and game['bookmakers']:
                            for m in game['bookmakers'][0]['markets']:
                                if m['key'] == 'correct_score':
                                    for o in m['outcomes']:
                                        if o['name'] == '0-0': odd_00 = o['price']
                        if odd_00:
                            api_results.append({
                                "Tijd": game_time,
                                "Wedstrijd": f"{game['home_team']} - {game['away_team']}",
                                "Odd": odd_00,
                                "Competitie": selected_name
                            })
                    if api_results:
                        st.session_state.last_scan = pd.DataFrame(api_results)
                        st.table(st.session_state.last_scan)
                    else:
                        st.warning("Geen actuele 0-0 odds gevonden voor deze competitie.")
                else:
                    st.error("API limiet bereikt of competitie niet beschikbaar.")
            except:
                st.error("Verbindingsfout.")

# --- TAB 2: HANDMATIG (OddsPortal Copy-Paste) ---
with tab2:
    st.subheader("OddsPortal Scraper (Thai League & Specials)")
    manual_comp = st.text_input("Naam van competitie:", "Thai League 1")
    input_data = st.text_area("Plak hier de tekst van OddsPortal:", height=150)
    
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
                            "Tijd": datetime.now().strftime("%d-%m %H:%M"),
                            "Wedstrijd": match_name, 
                            "Odd": max([float(o) for o in odds]), 
                            "Competitie": manual_comp
                        })
            if manual_results:
                st.session_state.last_scan = pd.DataFrame(manual_results)
                st.table(st.session_state.last_scan)
            else:
                st.error("Kon geen 0-0 patronen vinden. Kopieer de Correct Score tabel.")

# --- OPSLAAN SECTIE ---
if 'last_scan' in st.session_state:
    st.divider()
    st.subheader("💾 Bet toevoegen aan je archief")
    col_sel, col_bet = st.columns([2, 1])
    with col_sel:
        selected_match = st.selectbox("Welke wedstrijd heb je gespeeld?", st.session_state.last_scan['Wedstrijd'])
    with col_bet:
        inzet = st.number_input("Inzet (minimaal 1):", min_value=1.0, value=1.0, step=1.0)
        if st.button("BEVESTIG & OPSLAAN"):
            m_info = st.session_state.last_scan[st.session_state.last_scan['Wedstrijd'] == selected_match].iloc[0]
            nieuwe_rij = {
                "Tijdstip": m_info['Tijd'] if 'Tijd' in m_info else datetime.now().strftime("%H:%M"),
                "Competitie": m_info['Competitie'],
                "Wedstrijd": selected_match,
                "Odd": m_info['Odd'],
                "Inzet": inzet,
                "Pot. Winst": round(m_info['Odd'] * inzet, 2)
            }
            st.session_state.archief = pd.concat([st.session_state.archief, pd.DataFrame([nieuwe_rij])], ignore_index=True)
            st.toast(f"Bet op {selected_match} opgeslagen!")

# --- HET MASTER ARCHIEF ---
st.divider()
st.subheader("📊 Je Professionele Logboek")
if not st.session_state.archief.empty:
    st.dataframe(st.session_state.archief, use_container_width=True, hide_index=True)
    
    # Statistieken
    c1, c2 = st.columns(2)
    with c1:
        st.write(f"**Totaal aantal bets:** {len(st.session_state.archief)}")
    with c2:
        st.write(f"**Totaal risico:** {st.session_state.archief['Inzet'].sum()} units")
    
    # Export
    csv = st.session_state.archief.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Dagoverzicht (CSV)", csv, f"mijn_bets_{datetime.now().strftime('%d-%m')}.csv", "text/csv")
else:
    st.info("Je archief is momenteel leeg. Begin met scannen om je lijst op te bouwen.")
