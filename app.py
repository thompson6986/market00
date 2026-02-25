import streamlit as st
import requests
from datetime import datetime
import pandas as pd

API_KEY = '5890cd7c7251e5b9fe336d224e2b6bb4'

st.set_page_config(page_title="Deep Scan 0-0 Monitor", page_icon="⚽")

st.title("⚽ Global 0-0 Tracker")
st.caption("Scant alle beschikbare wereldwijde markten op 0-0 odds")

def get_all_00_odds():
    # We scannen 'soccer' (de hoofdgroep) voor alle aankomende wedstrijden
    url = f"https://api.the-odds-api.com/v4/sports/soccer/odds/"
    params = {
        'apiKey': API_KEY,
        'regions': 'eu',
        'markets': 'correct_score',
        'oddsFormat': 'decimal'
    }
    
    try:
        r = requests.get(url, params=params)
        if r.status_code != 200:
            return pd.DataFrame(), f"Fout: {r.status_code}"
            
        data = r.json()
        results = []
        
        for game in data:
            home = game['home_team']
            away = game['away_team']
            league = game['sport_title']
            raw_time = datetime.fromisoformat(game['commence_time'].replace('Z', ''))
            
            odd_00 = None
            if 'bookmakers' in game and game['bookmakers']:
                # We checken de eerste paar bookmakers voor de 0-0 odd
                for bm in game['bookmakers']:
                    for mkt in bm['markets']:
                        if mkt['key'] == 'correct_score':
                            for outcome in mkt['outcomes']:
                                if outcome['name'] == '0-0':
                                    odd_00 = outcome['price']
                                    break
                    if odd_00: break
            
            if odd_00:
                results.append({
                    "Tijd": raw_time.strftime('%H:%M (%d-%m)'),
                    "Competitie": league,
                    "Wedstrijd": f"{home} - {away}",
                    "Odd 0-0": odd_00,
                    "SortTime": raw_time
                })
        
        if not results:
            return pd.DataFrame(), "Geen 0-0 odds gevonden in de huidige scan."

        df = pd.DataFrame(results).sort_values(by="SortTime")
        return df.drop(columns=['SortTime']), None
    
    except Exception as e:
        return pd.DataFrame(), str(e)

if st.button('SCAN ALLE WERELDWIJDE MARKTEN'):
    with st.spinner('Bezig met diepe scan...'):
        df, error = get_all_00_odds()
        if error:
            st.error(error)
        elif not df.empty:
            st.success(f"Totaal {len(df)} wedstrijden met 0-0 odds gevonden.")
            # Filter optie voor de gebruiker
            search_term = st.text_input("Filter op land of team (bijv. 'Thai'):")
            if search_term:
                df = df[df.apply(lambda row: search_term.lower() in row.astype(str).str.lower().values, axis=1)]
            
            st.table(df)
        else:
            st.warning("Geen data gevonden.")

st.divider()
st.info("Let op: Als de Thai League hier niet tussen staat, levert de API deze specifieke markt vandaag helaas niet aan.")
