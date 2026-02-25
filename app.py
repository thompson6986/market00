import streamlit as st
import requests
from datetime import datetime
import pandas as pd

# JOUW PERSOONLIJKE API-KEY
API_KEY = '5890cd7c7251e5b9fe336d224e2b6bb4'

st.set_page_config(page_title="Pro 0-0 Monitor", page_icon="⚽", layout="wide")

# CSS voor een professionele look
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007bff; color: white; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚽ 0-0 Correct Score Tracker")
st.subheader("Gesoorteerd op speeltijd")

def get_data():
    # We halen de data op voor alle aankomende voetbalwedstrijden
    url = "https://api.the-odds-api.com/v4/sports/soccer/odds/"
    params = {
        'apiKey': API_KEY,
        'regions': 'eu',
        'markets': 'correct_score',
        'oddsFormat': 'decimal'
    }
    
    try:
        r = requests.get(url, params=params)
        if r.status_code != 200:
            st.error(f"API Fout: {r.status_code}. Controleer of je limiet niet bereikt is.")
            return pd.DataFrame()
            
        data = r.json()
        results = []
        
        for game in data:
            home = game['home_team']
            away = game['away_team']
            # Tijd verwerken
            raw_time = datetime.fromisoformat(game['commence_time'].replace('Z', ''))
            
            odd_00 = None
            if 'bookmakers' in game and len(game['bookmakers']) > 0:
                # We checken de eerste beschikbare bookmaker
                for market in game['bookmakers'][0]['markets']:
                    if market['key'] == 'correct_score':
                        for outcome in market['outcomes']:
                            if outcome['name'] == '0-0':
                                odd_00 = outcome['price']
                                break
            
            if odd_00:
                results.append({
                    "Tijd": raw_time.strftime('%H:%M (%d-%m)'),
                    "Wedstrijd": f"{home} vs {away}",
                    "Odd 0-0": odd_00,
                    "SortTime": raw_time
                })
        
        if not results:
            return pd.DataFrame()

        # Sorteren op tijd
        df = pd.DataFrame(results).sort_values(by="SortTime")
        return df.drop(columns=['SortTime'])
    
    except Exception as e:
        st.error(f"Er is iets misgegaan: {e}")
        return pd.DataFrame()

# Knop om de data te verversen
if st.button('🔄 HAAL LIVE ODDS OP'):
    with st.spinner('Bezig met scannen van markten...'):
        df = get_data()
        if not df.empty:
            st.success(f"Totaal {len(df)} wedstrijden gevonden met 0-0 odds.")
            # Tabel weergeven
            st.dataframe(
                df, 
                use_container_width=True, 
                hide_index=True
            )
        else:
            st.warning("Geen 0-0 odds beschikbaar op dit moment. Probeer het later opnieuw.")

st.divider()
st.caption(f"Systeem tijd: {datetime.now().strftime('%d-%m-%Y %H:%M')}")
