import streamlit as st
import requests
from datetime import datetime
import pandas as pd

API_KEY = '5890cd7c7251e5b9fe336d224e2b6bb4'

st.set_page_config(page_title="Thai League Finder", page_icon="🇹🇭")

st.title("🇹🇭 Thai League 0-0 Scanner")

def get_active_thai_keys():
    # Stap 1: Haal alle actieve sporten/competities op
    url = f"https://api.the-odds-api.com/v4/sports/?apiKey={API_KEY}"
    try:
        r = requests.get(url)
        all_leagues = r.json()
        # Zoek naar alles wat 'Thailand' bevat
        found = [l['key'] for l in all_leagues if 'thailand' in l['key'].lower()]
        return found
    except:
        return []

def get_odds(league_key):
    # Stap 2: Haal de odds op voor de gevonden key
    url = f"https://api.the-odds-api.com/v4/sports/{league_key}/odds/"
    params = {
        'apiKey': API_KEY,
        'regions': 'eu',
        'markets': 'correct_score',
        'oddsFormat': 'decimal'
    }
    r = requests.get(url, params=params)
    return r.json() if r.status_code == 200 else None

if st.button('ZOEK EN SCAN THAISE COMPETITIES'):
    with st.spinner('Bezig met zoeken naar actieve Thaise keys...'):
        thai_keys = get_active_thai_keys()
        
        if not thai_keys:
            st.error("De API heeft momenteel GEEN enkele Thaise competitie in de lijst staan.")
            st.info("Tip: Controleer op Flashscore of de wedstrijden wel door grote Europese bookmakers (zoals Bet365) worden aangeboden. Zo niet, dan heeft de API ze ook niet.")
        else:
            st.success(f"Gevonden keys: {', '.join(thai_keys)}")
            
            all_data = []
            for key in thai_keys:
                odds_data = get_odds(key)
                if odds_data:
                    for game in odds_data:
                        home = game['home_team']
                        away = game['away_team']
                        raw_time = datetime.fromisoformat(game['commence_time'].replace('Z', ''))
                        
                        odd_00 = None
                        if 'bookmakers' in game and game['bookmakers']:
                            for mkt in game['bookmakers'][0]['markets']:
                                if mkt['key'] == 'correct_score':
                                    for outcome in mkt['outcomes']:
                                        if outcome['name'] == '0-0':
                                            odd_00 = outcome['price']
                                            break
                        
                        if odd_00:
                            all_data.append({
                                "Tijd": raw_time.strftime('%H:%M (%d-%m)'),
                                "Wedstrijd": f"{home} - {away}",
                                "Odd 0-0": odd_00,
                                "SortTime": raw_time
                            })

            if all_data:
                df = pd.DataFrame(all_data).sort_values(by="SortTime")
                st.table(df.drop(columns=['SortTime']))
            else:
                st.warning("Competitie gevonden, maar de 0-0 markt is nog niet geopend door de bookmakers.")

st.divider()
st.write("Als dit niet werkt, is The-Odds-API niet de juiste bron voor de Thai League.")
