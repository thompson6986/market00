import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import itertools

# --- 1. CONFIGURATIE ---
st.set_page_config(page_title="Auto-Pilot Safe Bets", page_icon="🤖", layout="wide")
API_KEY = 'ae33f20cd78d0b2b015703ded3330fcb'

if 'archief' not in st.session_state:
    st.session_state.archief = pd.DataFrame(columns=["Datum_Tijd", "Combinatie", "Totale_Odd", "Status"])

st.title("🤖 Auto-Pilot Over 1.5 Generator")
st.markdown("Scant automatisch wereldwijde leagues naar veilige odds (**1.15 - 1.40**).")

# --- 2. DE SCANNER LOGICA ---
LEAGUES = {
    "Champions League": "soccer_uefa_champs_league",
    "Europa League": "soccer_uefa_europa_league",
    "Premier League": "soccer_epl",
    "Eredivisie": "soccer_netherlands_eredivisie",
    "Bundesliga": "soccer_germany_bundesliga",
    "La Liga": "soccer_spain_la_liga",
    "Serie A": "soccer_italy_serie_a",
    "Pro League (BE)": "soccer_belgium_first_division"
}

if st.button("🚀 SCAN INTERNATIONALE MARKTEN & GENEREER SLIPS"):
    all_valid_matches = []
    
    with st.spinner("Web afzoeken naar veilige Over 1.5 odds..."):
        for name, key in LEAGUES.items():
            url = f"https://api.the-odds-api.com/v4/sports/{key}/odds/"
            params = {
                'apiKey': API_KEY,
                'regions': 'eu',
                'markets': 'totals',
                'oddsFormat': 'decimal'
            }
            try:
                r = requests.get(url, params=params)
                if r.status_code == 200:
                    data = r.json()
                    for game in data:
                        # Tijdstip check
                        start = datetime.fromisoformat(game['commence_time'].replace('Z', '')).strftime('%d-%m %H:%M')
                        
                        if game['bookmakers']:
                            # We pakken de eerste betrouwbare bookmaker
                            for market in game['bookmakers'][0]['markets']:
                                if market['key'] == 'totals':
                                    for outcome in market['outcomes']:
                                        # Filter: Alleen Over 1.5 tussen 1.15 en 1.40
                                        if outcome['name'] == 'Over' and outcome['point'] == 1.5:
                                            odd = outcome['price']
                                            if 1.15 <= odd <= 1.40:
                                                all_valid_matches.append({
                                                    "Match": f"{game['home_team']} - {game['away_team']}",
                                                    "Odd": odd,
                                                    "League": name,
                                                    "Tijd": start
                                                })
            except:
                continue

    if all_valid_matches:
        st.success(f"Gevonden: {len(all_valid_matches)} wedstrijden die aan je criteria voldoen.")
        
        # --- AUTOMATISCH COMBINEREN ---
        valid_combos = []
        # We proberen combinaties van 2 en 3 games
        for r in [2, 3]:
            for combo in itertools.combinations(all_valid_matches, r):
                total_odd = 1.0
                for m in combo: total_odd *= m['Odd']
                
                # Check of de totale odd niet te hoog is (max 2.30)
                if 1.80 <= total_odd <= 2.30: # We voegen een minimum van 1.80 toe voor waarde
                    valid_combos.append({
                        "Games": " | ".join([f"{m['Match']} ({m['Odd']})" for m in combo]),
                        "Totale Odd": round(total_odd, 2),
                        "Aantal": r
                    })
        
        if valid_combos:
            st.subheader("🎯 Voorgestelde Safe Betslips")
            combo_df = pd.DataFrame(valid_combos).sort_values(by="Totale Odd", ascending=False)
            
            # Toon de top 10 veiligste combinaties
            st.dataframe(combo_df.head(10), use_container_width=True, hide_index=True)
            
            # Opslaan optie
            sel_slip = st.selectbox("Selecteer een gegenereerde slip om te volgen:", combo_df['Games'].head(10))
            if st.button("SLA SELECTIE OP IN DATABASE"):
                row = combo_df[combo_df['Games'] == sel_slip].iloc[0]
                new_entry = {
                    "Datum_Tijd": datetime.now().strftime("%d-%m %H:%M"),
                    "Combinatie": row['Games'],
                    "Totale_Odd": row['Totale Odd'],
                    "Status": "Actief"
                }
                st.session_state.archief = pd.concat([st.session_state.archief, pd.DataFrame([new_entry])], ignore_index=True)
                st.toast("Slip opgeslagen!")
        else:
            st.warning("Geen combinaties gevonden binnen de odd-range (max 2.30).")
    else:
        st.error("Geen individuele matches gevonden tussen 1.15 en 1.40. Probeer het later opnieuw.")

# --- 3. ARCHIEF ---
st.divider()
st.subheader("📊 Mijn Opgeslagen Database")
st.dataframe(st.session_state.archief, use_container_width=True, hide_index=True)

if not st.session_state.archief.empty:
    csv = st.session_state.archief.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Data", csv, "safe_bets.csv", "text/csv")
