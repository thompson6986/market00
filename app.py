import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import itertools

# --- 1. CONFIGURATIE ---
st.set_page_config(page_title="Pro Punter Dashboard", page_icon="⚖️", layout="wide")
API_KEY = 'ae33f20cd78d0b2b015703ded3330fcb'

# Initialiseer sessie-variabelen
if 'bet_history' not in st.session_state:
    st.session_state.bet_history = pd.DataFrame(columns=["Datum", "Type", "Wedstrijden", "Odd", "Resultaat", "Winst"])

if 'current_slips' not in st.session_state:
    st.session_state.current_slips = []

st.title("⚖️ Professional Betting Audit System")
st.markdown(f"**Handelsdag:** Woensdag 25 februari 2026")

# --- 2. SCANNER & GENERATOR ---
with st.sidebar:
    st.header("🔍 Markt Scanner")
    sport_selection = st.multiselect("Sporten:", ["soccer", "tennis", "basketball", "icehockey"], default=["soccer", "tennis"])
    scan_btn = st.button("🚀 SCAN ALLE MARKTEN")

if scan_btn:
    all_valid_matches = []
    vandaag_str = "2026-02-25"
    
    with st.spinner("Data verzamelen..."):
        # We scannen de meest actieve competities voor vandaag
        leagues = ["soccer_uefa_champs_league", "soccer_epl", "soccer_netherlands_eredivisie", "tennis_atp_dubai", "basketball_nba"]
        
        for key in leagues:
            url = f"https://api.the-odds-api.com/v4/sports/{key}/odds/"
            params = {'apiKey': API_KEY, 'regions': 'eu', 'markets': 'h2h,totals', 'oddsFormat': 'decimal'}
            try:
                r = requests.get(url, params=params)
                if r.status_code == 200:
                    data = r.json()
                    for game in data:
                        if vandaag_str in game['commence_time']:
                            tijd = datetime.fromisoformat(game['commence_time'].replace('Z', '')).strftime('%H:%M')
                            bm = game['bookmakers'][0] if game['bookmakers'] else None
                            if bm:
                                for market in bm['markets']:
                                    for outcome in market['outcomes']:
                                        price = outcome['price']
                                        if 1.12 <= price <= 1.45:
                                            label = f"{outcome['name']}" if market['key'] == 'h2h' else f"{outcome['name']} {outcome.get('point','')}"
                                            all_valid_matches.append({"Tijd": tijd, "Match": f"{game['home_team']} - {game['away_team']}", "Keuze": label, "Odd": price})
            except: continue

    if all_valid_matches:
        df_matches = pd.DataFrame(all_valid_matches).drop_duplicates(subset=['Match', 'Keuze'])
        match_pool = df_matches.to_dict('records')
        
        # Genereer de 4 types
        st.session_state.current_slips = []
        for target in [1.5, 2.0, 3.0, 5.0]:
            best_combo = None
            closest_diff = 999
            for r in range(2, 5):
                for combo in itertools.combinations(match_pool, r):
                    total_odd = 1.0
                    for m in combo: total_odd *= m['Odd']
                    if total_odd >= target and abs(total_odd - target) < closest_diff and total_odd <= (target * 1.3):
                        closest_diff = abs(total_odd - target)
                        best_combo = combo
                        final_odd = total_odd
            
            if best_combo:
                st.session_state.current_slips.append({
                    "Type": f"Target {target}",
                    "Matches": " | ".join([f"{m['Match']} ({m['Keuze']} @{m['Odd']})" for m in best_combo]),
                    "Odd": round(final_odd, 2)
                })

# --- 3. DISPLAY & SAVE ALL ---
if st.session_state.current_slips:
    st.subheader("📑 Nieuwe Betslips van Vandaag")
    cols = st.columns(4)
    for idx, slip in enumerate(st.session_state.current_slips):
        with cols[idx]:
            st.markdown(f"""<div style="background:#f0f2f6; padding:10px; border-radius:5px; height:250px">
            <b>{slip['Type']}</b><br><small>{slip['Matches']}</small><br><h3>@{slip['Odd']}</h3>
            </div>""", unsafe_allow_html=True)
    
    st.write("")
    if st.button("📥 SLA ALLE BOVENSTAANDE SLIPS OP IN ARCHIEF"):
        new_entries = []
        for s in st.session_state.current_slips:
            new_entries.append({
                "Datum": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Type": s['Type'],
                "Wedstrijden": s['Matches'],
                "Odd": s['Odd'],
                "Resultaat": "OPEN",
                "Winst": 0.0
            })
        st.session_state.bet_history = pd.concat([st.session_state.bet_history, pd.DataFrame(new_entries)], ignore_index=True)
        st.session_state.current_slips = [] # Leegmaken na opslaan
        st.success("Alle slips succesvol gearchiveerd!")
        st.rerun()

# --- 4. ARCHIEF & ROI TRACKING ---
st.divider()
st.subheader("📂 Professioneel Archief & Resultaten")

if not st.session_state.bet_history.empty:
    # ROI Berekening
    total_inzet = len(st.session_state.bet_history) * 1.0 # Uitgaande van 1 unit per bet
    totaal_winst = st.session_state.bet_history['Winst'].sum()
    roi = ((totaal_winst - total_inzet) / total_inzet) * 100 if total_inzet > 0 else 0
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Totaal Inzet", f"{total_inzet} Units")
    c2.metric("Netto Resultaat", f"{round(totaal_winst - total_inzet, 2)} Units")
    c3.metric("ROI %", f"{round(roi, 2)}%")

    # Tabel met resultaat-knop
    edited_df = st.data_editor(st.session_state.bet_history, use_container_width=True, hide_index=True)
    
    # Update winst op basis van status (In de data_editor kun je Status aanpassen naar WON)
    if st.button("🔄 Bereken Winst/Verlies"):
        for index, row in edited_df.iterrows():
            if row['Resultaat'] == "WON":
                edited_df.at[index, 'Winst'] = row['Odd']
            elif row['Resultaat'] == "LOST":
                edited_df.at[index, 'Winst'] = 0.0
        st.session_state.bet_history = edited_df
        st.rerun()

    csv = st.session_state.bet_history.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Database (Excel)", csv, "punter_database.csv", "text/csv")
else:
    st.info("Scan en sla slips op om je database te vullen.")
