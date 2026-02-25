import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import itertools

# --- CONFIGURATIE ---
st.set_page_config(page_title="Over 1.5 Bet Generator", page_icon="📈", layout="wide")
API_KEY = 'ae33f20cd78d0b2b015703ded3330fcb'

if 'archief' not in st.session_state:
    st.session_state.archief = pd.DataFrame(columns=["Datum_Tijd", "Combinatie", "Totale_Odd", "Inzet"])

st.title("📈 Safe Over 1.5 Bet Generator")
st.caption("Focus: Lage odds (1.15-1.40) | Max 3 games | Max slip odd 2.30")

# --- SIDEBAR: DATABASE ---
with st.sidebar:
    st.header("📂 Mijn Slips")
    if not st.session_state.archief.empty:
        csv = st.session_state.archief.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Database", csv, "over15_bets.csv", "text/csv")
        if st.button("🗑️ Wis Archief"):
            st.session_state.archief = pd.DataFrame(columns=["Datum_Tijd", "Combinatie", "Totale_Odd", "Inzet"])
            st.rerun()

# --- SELECTIE LEAGUES ---
league_options = {
    "Champions League": "soccer_uefa_champs_league",
    "Eredivisie": "soccer_netherlands_eredivisie",
    "Premier League": "soccer_epl",
    "Bundesliga": "soccer_germany_bundesliga",
    "Pro League (BE)": "soccer_belgium_first_division"
}
selected_leagues = st.multiselect("Selecteer competities om te scannen:", list(league_options.keys()), default=["Champions League"])

if st.button("GENEREER VEILIGE SLIPS"):
    all_matches = []
    
    with st.spinner("Scannen naar Over 1.5 markets..."):
        for league in selected_leagues:
            url = f"https://api.the-odds-api.com/v4/sports/{league_options[league]}/odds/"
            params = {'apiKey': API_KEY, 'regions': 'eu', 'markets': 'totals', 'oddsFormat': 'decimal'}
            r = requests.get(url, params=params)
            
            if r.status_code == 200:
                data = r.json()
                for game in data:
                    time = datetime.fromisoformat(game['commence_time'].replace('Z', '')).strftime('%d-%m %H:%M')
                    if game['bookmakers']:
                        for market in game['bookmakers'][0]['markets']:
                            if market['key'] == 'totals':
                                for outcome in market['outcomes']:
                                    # Filter op Over 1.5 en jouw odds range
                                    if outcome['name'] == 'Over' and outcome['point'] == 1.5:
                                        odd = outcome['price']
                                        if 1.15 <= odd <= 1.40:
                                            all_matches.append({
                                                "Match": f"{game['home_team']} - {game['away_team']}",
                                                "Odd": odd,
                                                "Tijd": time
                                            })
            else:
                st.error(f"Fout bij ophalen {league}. Code: {r.status_code}")

    if len(all_matches) < 2:
        st.warning("Te weinig wedstrijden gevonden die voldoen aan de 1.15 - 1.40 eis.")
    else:
        st.subheader("🎯 Voorgestelde Combinaties (Max 3 games, Max 2.30 odd)")
        
        # Genereer combinaties van 2 en 3 wedstrijden
        valid_combos = []
        for r in [2, 3]:
            for combo in itertools.combinations(all_matches, r):
                total_odd = 1
                for match in combo:
                    total_odd *= match['Odd']
                
                if total_odd <= 2.30:
                    valid_combos.append({
                        "Matches": " | ".join([m['Match'] for m in combo]),
                        "Details": " x ".join([str(m['Odd']) for m in combo]),
                        "Total_Odd": round(total_odd, 2)
                    })

        if valid_combos:
            combo_df = pd.DataFrame(valid_combos).sort_values(by="Total_Odd", ascending=False)
            st.dataframe(combo_df, use_container_width=True, hide_index=True)
            
            st.divider()
            st.subheader("💾 Slip Opslaan")
            sel_combo = st.selectbox("Kies een slip om op te slaan:", combo_df['Matches'])
            final_row = combo_df[combo_df['Matches'] == sel_combo].iloc[0]
            
            if st.button("Sla slip op in Archief"):
                new_entry = {
                    "Datum_Tijd": datetime.now().strftime("%d-%m %H:%M"),
                    "Combinatie": sel_combo,
                    "Totale_Odd": final_row['Total_Odd'],
                    "Inzet": 1.0
                }
                st.session_state.archief = pd.concat([st.session_state.archief, pd.DataFrame([new_entry])], ignore_index=True)
                st.success("Slip toegevoegd aan je database!")
        else:
            st.info("Geen combinaties gevonden die onder de 2.30 totale odd blijven.")

# --- ARCHIEF ---
st.divider()
st.subheader("📊 Opgeslagen Over 1.5 Database")
st.dataframe(st.session_state.archief, use_container_width=True, hide_index=True)
