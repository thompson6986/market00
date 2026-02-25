import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import itertools

# --- 1. CONFIGURATIE ---
st.set_page_config(page_title="Global Punter Generator", page_icon="🌎", layout="wide")
API_KEY = 'ae33f20cd78d0b2b015703ded3330fcb'

st.title("🌎 Full Global Today-Only Generator")
st.markdown(f"Datum: **Woensdag 25 februari 2026** | Focus: Alle actieve competities")

# --- 2. UITGEBREIDE LEAGUE LIJST ---
# We voegen hier zoveel mogelijk regio's toe voor maximale dekking
ALL_LEAGUES = {
    "Champions League": "soccer_uefa_champs_league",
    "Europa League": "soccer_uefa_europa_league",
    "Premier League": "soccer_epl",
    "Championship": "soccer_efl_champ",
    "League One": "soccer_england_league1",
    "League Two": "soccer_england_league2",
    "Eredivisie": "soccer_netherlands_eredivisie",
    "Bundesliga": "soccer_germany_bundesliga",
    "La Liga": "soccer_spain_la_liga",
    "Serie A": "soccer_italy_serie_a",
    "Pro League (BE)": "soccer_belgium_first_division",
    "Ligue 1": "soccer_france_ligue_one",
    "Primeira Liga (PT)": "soccer_portugal_primeira_liga",
    "Super Lig (TR)": "soccer_turkey_super_league",
    "Saudi Pro League": "soccer_saudi_pro_league",
    "Brazil Serie A": "soccer_brazil_campeonato",
    "Mexico Liga MX": "soccer_mexico_ligamx",
    "A-League (AU)": "soccer_australia_aleague",
    "Scottish Premiership": "soccer_spain_la_liga" # De API voegt soms regio's samen
}

if st.button("🚀 SCAN ALLE WERELDWIJDE MARKTEN"):
    all_valid_matches = []
    vandaag_str = "2026-02-25"
    
    # Voeg een voortgangsbalk toe voor de vele leagues
    progress_bar = st.progress(0)
    league_keys = list(ALL_LEAGUES.values())
    
    for i, key in enumerate(league_keys):
        url = f"https://api.the-odds-api.com/v4/sports/{key}/odds/"
        params = {'apiKey': API_KEY, 'regions': 'eu', 'markets': 'h2h,totals', 'oddsFormat': 'decimal'}
        
        try:
            r = requests.get(url, params=params)
            if r.status_code == 200:
                data = r.json()
                for game in data:
                    # Filter op vandaag
                    if vandaag_str in game['commence_time']:
                        tijd = datetime.fromisoformat(game['commence_time'].replace('Z', '')).strftime('%H:%M')
                        
                        if game['bookmakers']:
                            bm = game['bookmakers'][0]
                            for market in bm['markets']:
                                # Over 1.5 Safe Filter
                                if market['key'] == 'totals':
                                    for outcome in market['outcomes']:
                                        if outcome['name'] == 'Over' and outcome['point'] == 1.5:
                                            price = outcome['price']
                                            if 1.15 <= price <= 1.45:
                                                all_valid_matches.append({
                                                    "Tijd": tijd,
                                                    "Match": f"{game['home_team']} - {game['away_team']}",
                                                    "Odd": price,
                                                    "Markt": "Over 1.5",
                                                    "League": game['sport_title']
                                                })
                                # H2H Safe Filter
                                if market['key'] == 'h2h':
                                    for outcome in market['outcomes']:
                                        price = outcome['price']
                                        if 1.15 <= price <= 1.40:
                                            all_valid_matches.append({
                                                "Tijd": tijd,
                                                "Match": f"Winst {outcome['name']}",
                                                "Odd": price,
                                                "Markt": "H2H Safe",
                                                "League": game['sport_title']
                                            })
        except:
            continue
        progress_bar.progress((i + 1) / len(league_keys))

    if all_valid_matches:
        df = pd.DataFrame(all_valid_matches).drop_duplicates(subset=['Match'])
        st.success(f"Totaal {len(df)} veilige kansen gevonden in alle competities!")
        
        # Sorteer op tijd voor een professioneel overzicht
        df = df.sort_values(by="Tijd")
        st.dataframe(df, use_container_width=True, hide_index=True)

        # --- GENERATOR VOOR DE 4 BETSLIPS ---
        st.divider()
        st.subheader("📑 Jouw 4 Dagelijkse Betslips (Doel: 1.5, 2.0, 3.0, 5.0)")
        
        targets = [1.5, 2.0, 3.0, 5.0]
        match_pool = df.to_dict('records')
        cols = st.columns(4)

        for idx, target in enumerate(targets):
            with cols[idx]:
                st.markdown(f"### 🎯 Odd {target}")
                best_combo = None
                closest_diff = 999
                
                # We zoeken de beste combinatie van 2 of 3 wedstrijden
                for r in range(2, 4):
                    for combo in itertools.combinations(match_pool, r):
                        total_odd = 1.0
                        for m in combo: total_odd *= m['Odd']
                        
                        diff = abs(total_odd - target)
                        # We willen niet dat de odd lager is dan het doel
                        if total_odd >= target and diff < closest_diff and total_odd <= (target * 1.3):
                            closest_diff = diff
                            best_combo = combo
                            final_odd = total_odd
                
                if best_combo:
                    for m in best_combo:
                        st.write(f"⏱️ {m['Tijd']} - {m['Match']} ({m['Odd']})")
                    st.success(f"**Totaal: {round(final_odd, 2)}**")
                else:
                    st.write("Geen geschikte combinatie gevonden.")
    else:
        st.error("Geen resultaten. Mogelijk zijn de meeste wedstrijden van vandaag al begonnen of nog niet live in de API.")
