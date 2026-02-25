import streamlit as st
import requests
from datetime import datetime
import pandas as pd

API_KEY = '5890cd7c7251e5b9fe336d224e2b6bb4'

st.set_page_config(page_title="Pro 0-0 Monitor", page_icon="⚽")

st.title("⚽ Thai League 0-0 Tracker")

def get_thai_leagues():
    # Haal alle actieve voetbalcompetities op
    url = f"https://api.the-odds-api.com/v4/sports/?apiKey={API_KEY}"
    try:
        r = requests.get(url)
        all_sports = r.json()
        # Filter op voetbal en Thailand
        thai_leagues = [s['key'] for s in all_sports if 'soccer' in s['key'] and 'thailand' in s['key'].lower()]
        return thai_leagues
    except:
        return []

def get_odds(league_key):
    url = f"https://api.the-odds-api.com/v4/sports/{league_key}/odds/"
    params = {
        'apiKey': API_KEY,
        'regions': 'eu',
        'markets': 'correct_score',
        'oddsFormat': 'decimal'
    }
    r = requests.get(url, params=params)
    if r.status_code == 200:
        return r.json()
    return []

if st.button('SCAN THAISE MARKTEN'):
    with st.spinner('Zoeken naar Thaise competities...'):
        thai_keys = get_thai_leagues()
        
        if not thai_keys:
            st.warning("De API biedt momenteel geen Thaise competities aan. Dit gebeurt vaak op dagen dat er geen wedstrijden zijn.")
        else:
            all_results = []
            for key in thai_keys:
                data = get_odds(key)
                for game in data:
                    home = game['home_team']
                    away = game['away_team']
                    raw_time = datetime.fromisoformat(game['commence_time'].replace('Z', ''))
                    
                    odd_00 = None
                    if 'bookmakers' in game:
                        for bm in game['bookmakers']:
                            for mkt in bm['markets']:
                                if mkt['key'] == 'correct_score':
                                    for outcome in mkt['outcomes']:
                                        if outcome['name'] == '0-0':
                                            odd_00 = outcome['price']
                                            break
                            if odd_00: break
                    
                    if odd_00:
                        all_results.append({
                            "Tijd": raw_time.strftime('%H:%M (%d-%m)'),
                            "Wedstrijd": f"{home} - {away}",
                            "Odd 0-0": odd_00,
                            "SortTime": raw_time
                        })

            if all_results:
                df = pd.DataFrame(all_results).sort_values(by="SortTime")
                st.success(f"Gevonden in {', '.join(thai_keys)}:")
                st.table(df.drop(columns=['SortTime']))
            else:
                st.info(f"Thaise leagues gevonden ({', '.join(thai_keys)}), maar bookmakers hebben de 0-0 markt nog niet geopend.")

st.divider()
st.caption("Professionele Tip: De Thai League 1 speelt vaak in het weekend. Doordeweeks zijn er minder markten beschikbaar.")
