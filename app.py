import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import itertools

# --- 1. CONFIGURATIE ---
st.set_page_config(page_title="Pro Over 1.5 Generator", page_icon="📈", layout="wide")
API_KEY = 'ae33f20cd78d0b2b015703ded3330fcb'

if 'archief' not in st.session_state:
    st.session_state.archief = pd.DataFrame(columns=["Datum_Tijd", "Combinatie", "Totale_Odd", "Inzet"])

if 'manual_matches' not in st.session_state:
    st.session_state.manual_matches = []

st.title("📈 Safe Over 1.5 Bet Generator")
st.caption("Focus: 1.15-1.40 per game | Max 3 games | Max slip odd 2.30")

# --- 2. SIDEBAR: DATA BEHEER ---
with st.sidebar:
    st.header("📂 Mijn Database")
    if not st.session_state.archief.empty:
        st.write(f"Opgeslagen slips: **{len(st.session_state.archief)}**")
        csv = st.session_state.archief.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download CSV", csv, "over15_results.csv", "text/csv")
        
        st.divider()
        if st.button("🗑️ Wis Alles"):
            st.session_state.archief = pd.DataFrame(columns=["Datum_Tijd", "Combinatie", "Totale_Odd", "Inzet"])
            st.session_state.manual_matches = []
            st.rerun()

# --- 3. INPUT SECTIE ---
tab1, tab2 = st.tabs(["🚀 API Scan (Grote Leagues)", "➕ Handmatige Match Toevoegen"])

with tab1:
    league_options = {
        "Champions League": "soccer_uefa_champs_league",
        "Eredivisie": "soccer_netherlands_eredivisie",
        "Premier League": "soccer_epl",
        "Bundesliga": "soccer_germany_bundesliga",
        "Pro League (BE)": "soccer_belgium_first_division"
    }
    selected_leagues = st.multiselect("Scan deze competities:", list(league_options.keys()), default=["Champions League"])
    scan_btn = st.button("START SCAN")

with tab2:
    st.subheader("Voeg een match toe die niet in de API staat")
    c1, c2 = st.columns(2)
    with c1:
        m_name = st.text_input("Wedstrijd Naam:", placeholder="bijv. Ajax - PSV")
    with c2:
        m_odd = st.number_input("Over 1.5 Odd:", min_value=1.0, max_value=5.0, value=1.25, step=0.01)
    
    if st.button("Voeg toe aan wachtrij"):
        if m_name:
            st.session_state.manual_matches.append({"Match": m_name, "Odd": m_odd, "Tijd": "Handmatig"})
            st.success(f"{m_name} toegevoegd!")

# --- 4. LOGICA & GENERATOR ---
all_matches = []

# Voeg handmatige matches toe
all_matches.extend(st.session_state.manual_matches)

if scan_btn:
    with st.spinner("Scannen naar Over 1.5 markten..."):
        for league in selected_leagues:
            url = f"https://api.the-odds-api.com/v4/sports/{league_options[league]}/odds/"
            params = {'apiKey': API_KEY, 'regions': 'eu', 'markets': 'totals', 'oddsFormat': 'decimal'}
            try:
                r = requests.get(url, params=params)
                if r.status_code == 200:
                    data = r.json()
                    for game in data:
                        time = datetime.fromisoformat(game['commence_time'].replace('Z', '')).strftime('%d-%m %H:%M')
                        if game['bookmakers']:
                            for market in game['bookmakers'][0]['markets']:
                                if market['key'] == 'totals':
                                    for outcome in market['outcomes']:
                                        if outcome['name'] == 'Over' and outcome['point'] == 1.5:
                                            odd = outcome['price']
                                            if 1.15 <= odd <= 1.40:
                                                all_matches.append({"Match": f"{game['home_team']} - {game['away_team']}", "Odd": odd, "Tijd": time})
            except:
                st.error(f"Fout bij {league}")

# Toon alle gevonden/toegevoegde matches
if all_matches:
    st.divider()
    st.subheader("📋 Beschikbare Wedstrijden (1.15 - 1.40)")
    st.table(pd.DataFrame(all_matches))

    # Genereer combinaties
    valid_combos = []
    for r in [2, 3]: # Combos van 2 en 3
        for combo in itertools.combinations(all_matches, r):
            total_odd = 1
            for match in combo:
                total_odd *= match['Odd']
            
            if total_odd <= 2.30:
                valid_combos.append({
                    "Combinatie": " + ".join([m['Match'] for m in combo]),
                    "Odds": " x ".join([str(m['Odd']) for m in combo]),
                    "Totale Odd": round(total_odd, 2)
                })

    if valid_combos:
        st.subheader("🎯 Beste Slip Combinaties")
        combo_df = pd.DataFrame(valid_combos).sort_values(by="Totale Odd", ascending=False)
        st.dataframe(combo_df, use_container_width=True, hide_index=True)
        
        sel_final = st.selectbox("Selecteer een slip om te bewaren:", combo_df['Combinatie'])
        final_data = combo_df[combo_df['Combinatie'] == sel_final].iloc[0]
        
        if st.button("SLA SLIP OP"):
            new_row = {
                "Datum_Tijd": datetime.now().strftime("%d-%m %H:%M"),
                "Combinatie": sel_final,
                "Totale_Odd": final_data['Totale Odd'],
                "Inzet": 1.0
            }
            st.session_state.archief = pd.concat([st.session_state.archief, pd.DataFrame([new_row])], ignore_index=True)
            st.toast("Geregistreerd in CSV!")
    else:
        st.info("Geen combinaties gevonden die aan de eisen voldoen.")
