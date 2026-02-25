import streamlit as st
import requests
from datetime import datetime
import pandas as pd

API_KEY = '5890cd7c7251e5b9fe336d224e2b6bb4'

st.set_page_config(page_title="Pro 0-0 Monitor", page_icon="⚽")

st.title("⚽ 0-0 Correct Score Tracker")

# Bijgewerkte lijst met de Thai League 1 bovenaan
league_options = {
    'Thai League 1 (Tha)': 'soccer_thailand_thai_league_1',
    'Eredivisie (Ned)': 'soccer_netherlands_eredivisie',
    'Premier League (Eng)': 'soccer_epl',
    'La Liga (Spa)': 'soccer_spain_la_liga',
    'Serie A (Ita)': 'soccer_italy_serie_a',
    'Bundesliga (Dui)': 'soccer_germany_bundesliga',
    'Ligue 1 (Fra)': 'soccer_france_ligue_one'
}

selected_league = st.selectbox("Kies een competitie:", list(league_options.keys()))
league_id = league_options[selected_league]

def get_data(chosen_league):
    url = f"https://api.the-odds-api.com/v4/sports/{chosen_league}/odds/"
    params = {
        'apiKey': API_KEY,
        'regions': 'eu',
        'markets': 'correct_score',
        'oddsFormat': 'decimal'
    }
    
    try:
        r = requests.get(url, params=params)
        
        # Specifieke check voor de 422 fout (vaak is de league dan niet beschikbaar in de API)
        if r.status_code == 422:
            st.warning(f"De competitie '{chosen_league}' is momenteel niet beschikbaar in de API. Dit kan gebeuren als er de komende dagen geen wedstrijden gepland staan.")
            return pd.DataFrame()
        elif r.status_code != 200:
            st.error(f"API Fout {r.status_code}: {r.text}")
            return pd.DataFrame()
            
        data = r.json()
        results = []
        
        for game in data:
            home = game['home_team']
            away = game['away_team']
            raw_time = datetime.fromisoformat(game['commence_time'].replace('Z', ''))
            
            odd_00 = None
            if 'bookmakers' in game and len(game['bookmakers']) > 0:
                for bookmaker in game['bookmakers']:
                    for market in bookmaker['markets']:
                        if market['key'] == 'correct_score':
                            # Zoek specifiek naar 0-0
                            for outcome in market['outcomes']:
                                if outcome['name'] == '0-0':
                                    odd_00 = outcome['price']
                                    break
                    if odd_00: break 
            
            if odd_00:
                results.append({
                    "Tijd": raw_time.strftime('%H:%M (%d-%m)'),
                    "Wedstrijd": f"{home} - {away}",
                    "Odd 0-0": odd_00,
                    "SortTime": raw_time
                })
        
        if not results:
            return pd.DataFrame()

        df = pd.DataFrame(results).sort_values(by="SortTime")
        return df.drop(columns=['SortTime'])
    
    except Exception as e:
        st.error(f"Fout: {e}")
        return pd.DataFrame()

if st.button('HAAL ODDS OP'):
    with st.spinner(f'Scannen van {selected_league}...'):
        df = get_data(league_id)
        if not df.empty:
            st.success(f"Gevonden resultaten voor {selected_league}:")
            st.table(df)
        else:
            st.info(f"Geen 0-0 odds gevonden voor {selected_league}. Dit kan betekenen dat de bookmakers de 'Correct Score' markt voor deze competitie nog niet hebben geopend.")

st.divider()
st.caption(f"Status: Verbonden met API | Datum: {datetime.now().strftime('%d-%m-%Y')}")
