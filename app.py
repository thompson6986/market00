import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import itertools

# --- CONFIGURATIE ---
st.set_page_config(page_title="Pro Punter Dashboard", page_icon="⚖️", layout="wide")
API_KEY = 'ae33f20cd78d0b2b015703ded3330fcb'
SHEET_URL = "https://docs.google.com/spreadsheets/d/10F4xl7dcHIpfN1xdLrZ2BNAn532OJk0_58ErD51rRE4/edit?usp=sharing"

st.title("⚖️ Professional Betting Generator")
st.markdown(f"**Bestand:** [Pro Bet Tracker]({SHEET_URL})")

if 'display_slips' not in st.session_state:
    st.session_state.display_slips = [] # Voor de visuele kaarten
if 'export_data' not in st.session_state:
    st.session_state.export_data = []  # Voor de Google Sheets rijen

with st.sidebar:
    st.header("🔍 Scanner")
    scan_btn = st.button("🚀 GENEREER SLIPS (ONDER ELKAAR)")

if scan_btn:
    all_valid_matches = []
    vandaag_str = "2026-02-25"
    leagues = ["soccer_uefa_champs_league", "soccer_epl", "soccer_netherlands_eredivisie", "tennis_atp_dubai", "basketball_nba"]
    
    with st.spinner("Markten scannen..."):
        for key in leagues:
            url = f"https://api.the-odds-api.com/v4/sports/{key}/odds/"
            params = {'apiKey': API_KEY, 'regions': 'eu', 'markets': 'h2h,totals', 'oddsFormat': 'decimal'}
            try:
                r = requests.get(url, params=params)
                if r.status_code == 200:
                    for game in r.json():
                        if vandaag_str in game['commence_time']:
                            tijd = datetime.fromisoformat(game['commence_time'].replace('Z', '')).strftime('%H:%M')
                            if game['bookmakers']:
                                for market in game['bookmakers'][0]['markets']:
                                    for outcome in market['outcomes']:
                                        price = outcome['price']
                                        if 1.12 <= price <= 1.45:
                                            label = f"{outcome['name']}" if market['key'] == 'h2h' else f"{outcome['name']} {outcome.get('point','')}"
                                            all_valid_matches.append({
                                                "Tijd": tijd,
                                                "Team": f"{game['home_team']} - {game['away_team']}",
                                                "Selectie": label,
                                                "Odd": price
                                            })
            except: continue

    if all_valid_matches:
        pool = pd.DataFrame(all_valid_matches).drop_duplicates(subset=['Team', 'Selectie']).to_dict('records')
        st.session_state.display_slips = []
        st.session_state.export_data = []
        
        for target in [1.5, 2.0, 3.0, 5.0]:
            best_combo, closest_diff = None, 999
            for r in range(2, 5):
                for combo in itertools.combinations(pool, r):
                    total_odd = 1.0
                    for m in combo: total_odd *= m['Odd']
                    if total_odd >= target and abs(total_odd - target) < closest_diff and total_odd <= (target * 1.3):
                        closest_diff = abs(total_odd - target)
                        best_combo, final_odd = combo, round(total_odd, 2)
            
            if best_combo:
                # 1. Opslaan voor de visuele kaarten (gegroepeerd)
                st.session_state.display_slips.append({"Type": f"Target {target}", "Matches": best_combo, "Total": final_odd})
                
                # 2. Opslaan voor Google Sheets (onder elkaar)
                for i, m in enumerate(best_combo):
                    st.session_state.export_data.append({
                        "Datum": datetime.now().strftime("%d-%m-%Y"),
                        "Slip_ID": f"Target {target} (@{final_odd})",
                        "Tijd": m['Tijd'],
                        "Wedstrijd": m['Team'],
                        "Keuze": m['Selectie'],
                        "Odd": m['Odd'],
                        "Status": "OPEN"
                    })
                # Voeg een lege regel toe tussen de slips voor de leesbaarheid
                st.session_state.export_data.append({k: "" for k in ["Datum", "Slip_ID", "Tijd", "Wedstrijd", "Keuze", "Odd", "Status"]})

# --- DISPLAY ---
if st.session_state.display_slips:
    cols = st.columns(4)
    for idx, s in enumerate(st.session_state.display_slips):
        with cols[idx]:
            st.markdown(f"### 🎯 {s['Type']}")
            for m in s['Matches']:
                st.write(f"⏱ {m['Tijd']} | {m['Team']}\n`{m['Selectie']} @{m['Odd']}`")
            st.success(f"**Totaal: @{s['Total']}**")
    
    st.divider()
    # Export knop
    df_export = pd.DataFrame(st.session_state.export_data)
    csv = df_export.to_csv(index=False).encode('utf-8')
    st.download_button("📥 DOWNLOAD VOOR GOOGLE SHEETS (RIJEN)", csv, "verticale_bets.csv", "text/csv")
    st.caption("Importeer dit bestand in Sheets. Elke wedstrijd krijgt nu zijn eigen rij onder de juiste Slip ID.")
