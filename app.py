import streamlit as st
import requests
from datetime import datetime
import pandas as pd

API_KEY = '5890cd7c7251e5b9fe336d224e2b6bb4'

st.set_page_config(page_title="Pro 0-0 Monitor", page_icon="⚽")

st.title("⚽ Professional 0-0 Tracker")

# Een lijst met betrouwbare league-keys voor de API
leagues = {
    "Thailand League 1": "soccer_thailand_thai_league_1",
    "Eredivisie (NL)": "soccer_netherlands_eredivisie",
    "J-League (Japan)": "soccer_japan_j_league",
    "K-League (Z-Korea)": "soccer_south_korea_k_league_1",
    "Premier League (UK)": "soccer_epl",
    "Championship (UK)": "soccer_efl_champ",
    "Serie A (IT)": "soccer_italy_serie_a"
}

target_league = st.selectbox("Selecteer de competitie die je wilt scannen:", list(leagues.keys()))
league_id = leagues[target_league]

def get_odds_safe(chosen_id):
    url = f"https://api.the-odds-api.com/v4/sports/{chosen_id}/odds/"
    params = {
        'apiKey': API_KEY,
        'regions': 'eu',
        'markets': 'correct_score',
        'oddsFormat': 'decimal'
    }
    
    r = requests.get(url, params=params)
    
    if r.status_code == 422:
        return None, "De API weigert dit verzoek (422). Deze competitie is momenteel niet actief of te groot."
    if r.status_code != 200:
        return None, f"Fout {r.status_code}: {r.text}"
        
    return r.json(), None

if st.button(f'SCAN {target_league.upper()}'):
    with st.spinner('Data ophalen...'):
        data, error = get_odds_safe(league_id)
        
        if error:
            st.error(error)
        elif data:
            results = []
            for game in data:
                home = game['home_team']
                away = game['away_team']
                raw_time = datetime.fromisoformat(game['commence_time'].replace('Z', ''))
                
                odd_00 = None
                if 'bookmakers' in game and game['bookmakers']:
                    # Check de eerste beschikbare bookmaker voor de 0-0
                    for market in game['bookmakers'][0]['markets']:
                        if market['key'] == 'correct_score':
                            for outcome in market['outcomes']:
                                if outcome['name'] == '0-0':
                                    odd_00 = outcome['price']
                                    break
                
                if odd_00:
                    results.append({
                        "Tijd": raw_time.strftime('%H:%M (%d-%m)'),
                        "Wedstrijd": f"{home} - {away}",
                        "Odd 0-0": odd_00,
                        "SortTime": raw_time
                    })

            if results:
                df = pd.DataFrame(results).sort_values(by="SortTime")
                st.success(f"Resultaten voor {target_league}:")
                st.table(df.drop(columns=['SortTime']))
            else:
                st.warning(f"Geen 0-0 odds gevonden voor {target_league}. Bookmakers hebben deze markt nog niet open.")
        else:
            st.info("Geen data ontvangen.")

st.divider()
st.caption("Let op: Voor de Thai League verschijnen de odds vaak pas op de wedstrijddag zelf.")
