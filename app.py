import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import itertools

# --- 1. CONFIGURATIE ---
st.set_page_config(page_title="Auto-Pilot Safe Bets", page_icon="🤖", layout="wide")
API_KEY = 'ae33f20cd78d0b2b015703ded3330fcb'

if 'archief' not in st.session_state:
    st.session_state.archief = pd.DataFrame(columns=["Datum_Tijd", "Combinatie", "Totale_Odd", "Markt"])

st.title("🤖 Auto-Pilot Multi-Market Generator")
st.markdown("Scant nu zowel **Over 1.5** als **Top Favorieten (H2H)** tussen 1.15 en 1.40.")

# --- 2. DE SCANNER LOGICA ---
LEAGUES = {
    "Champions League": "soccer_uefa_champs_league",
    "Europa League": "soccer_uefa_europa_league",
    "Premier League": "soccer_epl",
    "Eredivisie": "soccer_netherlands_eredivisie",
    "Bundesliga": "soccer_germany_bundesliga",
    "La Liga": "soccer_spain_la_liga",
    "Serie A": "soccer_italy_serie_a",
    "Pro League (BE)": "soccer_belgium_first_division",
    "Ligue 1 (FR)": "soccer_france_ligue_one"
}

if st.button("🚀 START WERELDWIJDE SCAN"):
    all_valid_matches = []
    
    with st.spinner("Scannen van alle markten op 1.15 - 1.40..."):
        for name, key in LEAGUES.items():
            # We scannen zowel 'h2h' als 'totals' om de kans op matches te vergroten
            url = f"https://api.the-odds-api.com/v4/sports/{key}/odds/"
            params = {'apiKey': API_KEY, 'regions': 'eu', 'markets': 'h2h,totals', 'oddsFormat': 'decimal'}
            
            try:
                r = requests.get(url, params=params)
                if r.status_code == 200:
                    data = r.json()
                    for game in data:
                        start = datetime.fromisoformat(game['commence_time'].replace('Z', '')).strftime('%d-%m %H:%M')
                        
                        if game['bookmakers']:
                            bm = game['bookmakers'][0]
                            for market in bm['markets']:
                                # CHECK 1: OVER 1.5 GOALS
                                if market['key'] == 'totals':
                                    for outcome in market['outcomes']:
                                        if outcome['name'] == 'Over' and outcome['point'] == 1.5:
                                            odd = outcome['price']
                                            if 1.15 <= odd <= 1.40:
                                                all_valid_matches.append({"Match": f"{game['home_team']} - {game['away_team']}", "Odd": odd, "Market": "Over 1.5", "Tijd": start})
                                
                                # CHECK 2: STERKE FAVORIET (Winst)
                                if market['key'] == 'h2h':
                                    for outcome in market['outcomes']:
                                        odd = outcome['price']
                                        if 1.15 <= odd <= 1.40:
                                            all_valid_matches.append({"Match": f"Winst: {outcome['name']}", "Odd": odd, "Market": "H2H Safe", "Tijd": start})
            except:
                continue

    if all_valid_matches:
        # Verwijder duplicaten en toon resultaten
        matches_df = pd.DataFrame(all_valid_matches).drop_duplicates(subset=['Match'])
        st.success(f"{len(matches_df)} veilige opties gevonden!")
        st.table(matches_df)

        # --- COMBINATIES GENEREREN ---
        valid_combos = []
        matches_list = matches_df.to_dict('records')
        
        for r in [2, 3]:
            for combo in itertools.combinations(matches_list, r):
                total_odd = 1.0
                for m in combo: total_odd *= m['Odd']
                
                if 1.60 <= total_odd <= 2.30:
                    valid_combos.append({
                        "Combinatie": " + ".join([f"{m['Match']} ({m['Odd']})" for m in combo]),
                        "Totale Odd": round(total_odd, 2),
                        "Markten": " & ".join(list(set([m['Market'] for m in combo])))
                    })
        
        if valid_combos:
            st.subheader("🎯 Automatisch Gegenereerde Slips")
            combo_df = pd.DataFrame(valid_combos).sort_values(by="Totale Odd", ascending=False)
            st.dataframe(combo_df.head(15), use_container_width=True, hide_index=True)
            
            # Opslaan
            sel = st.selectbox("Selecteer slip voor database:", combo_df['Combinatie'].head(15))
            if st.button("SLA SLIP OP"):
                row = combo_df[combo_df['Combinatie'] == sel].iloc[0]
                new_entry = {"Datum_Tijd": datetime.now().strftime("%d-%m %H:%M"), "Combinatie": row['Combinatie'], "Totale_Odd": row['Totale Odd'], "Markt": row['Markten']}
                st.session_state.archief = pd.concat([st.session_state.archief, pd.DataFrame([new_entry])], ignore_index=True)
                st.toast("Opgeslagen!")
    else:
        st.error("Nog steeds geen matches gevonden. Dit kan betekenen dat er op dit moment (woensdagmiddag) geen topfavorieten spelen of de marktdata nog niet is vrijgegeven.")

# --- ARCHIEF ---
st.divider()
st.subheader("📊 Mijn Database")
st.dataframe(st.session_state.archief, use_container_width=True, hide_index=True)
