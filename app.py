import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import itertools

# --- 1. CONFIGURATIE ---
st.set_page_config(page_title="Pro Punter Dashboard", page_icon="⚖️", layout="wide")
API_KEY = 'ae33f20cd78d0b2b015703ded3330fcb'

# JOUW PERSOONLIJKE LINK IS HIER INGEVULD
SHEET_URL = "https://docs.google.com/spreadsheets/d/10F4xl7dcHIpfN1xdLrZ2BNAn532OJk0_58ErD51rRE4/edit?usp=sharing"

st.title("⚖️ Professional Today-Only Generator")
st.markdown(f"**Gekoppeld bestand:** [Open Pro Bet Tracker]({SHEET_URL})")
st.caption("Doel: 4 betslips (1.5, 2, 3, 5) | Focus op berekende risico's")

# Initialiseer sessie
if 'current_slips' not in st.session_state:
    st.session_state.current_slips = []

# --- 2. MULTI-SPORT SCANNER ---
with st.sidebar:
    st.header("🔍 Markt Scanner")
    st.info("Scant voetbal, tennis en basketbal op odds tussen 1.12 en 1.45.")
    scan_btn = st.button("🚀 GENEREER SLIPS VOOR VANDAAG")

if scan_btn:
    all_valid_matches = []
    vandaag_str = "2026-02-25"
    
    # Lijst van competities voor een brede scan vandaag
    leagues = [
        "soccer_uefa_champs_league", "soccer_epl", "soccer_netherlands_eredivisie", 
        "soccer_spain_la_liga", "soccer_germany_bundesliga", "soccer_italy_serie_a",
        "tennis_atp_dubai", "basketball_nba", "basketball_euroleague"
    ]
    
    with st.spinner("Data verzamelen uit mondiale markten..."):
        for key in leagues:
            url = f"https://api.the-odds-api.com/v4/sports/{key}/odds/"
            params = {'apiKey': API_KEY, 'regions': 'eu', 'markets': 'h2h,totals', 'oddsFormat': 'decimal'}
            try:
                r = requests.get(url, params=params)
                if r.status_code == 200:
                    data = r.json()
                    for game in data:
                        # Alleen wedstrijden van vandaag
                        if vandaag_str in game['commence_time']:
                            tijd = datetime.fromisoformat(game['commence_time'].replace('Z', '')).strftime('%H:%M')
                            if game['bookmakers']:
                                # Pak de odds van de eerste beschikbare bookmaker
                                for market in game['bookmakers'][0]['markets']:
                                    for outcome in market['outcomes']:
                                        price = outcome['price']
                                        # Professional Safe Range: 1.12 - 1.45
                                        if 1.12 <= price <= 1.45:
                                            # Filter voor totals (geen onrealistische lijnen)
                                            if market['key'] == 'totals' and outcome['point'] > 2.5 and "soccer" in key:
                                                continue
                                                
                                            label = f"{outcome['name']}" if market['key'] == 'h2h' else f"{outcome['name']} {outcome.get('point','')}"
                                            all_valid_matches.append({
                                                "Tijd": tijd,
                                                "Match": f"{game['home_team']} - {game['away_team']}",
                                                "Keuze": label,
                                                "Odd": price
                                            })
            except:
                continue

    if all_valid_matches:
        df_matches = pd.DataFrame(all_valid_matches).drop_duplicates(subset=['Match', 'Keuze'])
        match_pool = df_matches.to_dict('records')
        st.session_state.current_slips = []
        
        # Genereer de 4 verplichte betslips per categorie
        for target in [1.5, 2.0, 3.0, 5.0]:
            best_combo, closest_diff = None, 999
            # Probeer combinaties van 2 tot 4 wedstrijden
            for r in range(2, 5):
                for combo in itertools.combinations(match_pool, r):
                    total_odd = 1.0
                    for m in combo: total_odd *= m['Odd']
                    
                    diff = abs(total_odd - target)
                    # Odd moet minimaal het target zijn en niet extreem veel hoger (max 30% erover)
                    if total_odd >= target and diff < closest_diff and total_odd <= (target * 1.3):
                        closest_diff = diff
                        best_combo, final_odd = combo, round(total_odd, 2)
            
            if best_combo:
                st.session_state.current_slips.append({
                    "Datum": datetime.now().strftime("%d-%m-%Y %H:%M"),
                    "Type": f"Target {target}", 
                    "Wedstrijden": " | ".join([f"{m['Tijd']} {m['Match']} ({m['Keuze']} @{m['Odd']})" for m in best_combo]), 
                    "Odd": final_odd,
                    "Status": "OPEN"
                })

# --- 3. DISPLAY & EXPORT ---
if st.session_state.current_slips:
    st.subheader("📑 Jouw 4 Betslips voor Vandaag")
    cols = st.columns(4)
    for idx, slip in enumerate(st.session_state.current_slips):
        with cols[idx]:
            st.info(f"**{slip['Type']}**\n\n{slip['Wedstrijden']}\n\n**Totaal: @{slip['Odd']}**")
    
    st.divider()
    st.subheader("📤 Administratie")
    st.write("Sla deze slips op om ze in je Google Sheet te importeren.")
    
    df_save = pd.DataFrame(st.session_state.current_slips)
    csv = df_save.to_csv(index=False).encode('utf-8')
    
    st.download_button(
        label="📥 DOWNLOAD VOOR PRO BET TRACKER",
        data=csv,
        file_name=f"betslips_{datetime.now().strftime('%d_%m')}.csv",
        mime="text/csv",
    )
    st.markdown(f"**Instructie:** Open je [Google Sheet]({SHEET_URL}), ga naar **Bestand > Importeren > Uploaden** en kies dit bestand.")

else:
    st.info("Klik op de knop in de zijbalk om de slips voor vandaag te genereren.")
