import streamlit as st

import requests

from datetime import datetime

import pandas as pd



# CONFIGURATIE - Plak hier je eigen key

'778198466:AAEgHGVSkl_iLdT2zmW0VZFW7k834-8UmLY'



st.set_page_config(page_title="Pro Punter 0-0 Tracker", layout="wide")



st.title("⚽ Live 0-0 Correct Score Tracker")

st.caption("Gereserveerd voor professionele punters - Sortering op tijd")



def get_data():

    # We halen de belangrijkste Europese leagues op voor de beste liquiditeit

    # Je kunt 'soccer' gebruiken voor ALLES, maar dat verbruikt meer API-credits

    url = f"https://api.the-odds-api.com/v4/sports/soccer/odds/"

    params = {

        'apiKey': API_KEY,

        'regions': 'eu',

        'markets': 'correct_score',

        'oddsFormat': 'decimal'

    }

    

    try:

        r = requests.get(url, params=params)

        data = r.json()

        

        results = []

        for game in data:

            home = game['home_team']

            away = game['away_team']

            start_time = datetime.fromisoformat(game['commence_time'].replace('Z', ''))

            

            # Zoek de 0-0 odd bij de eerste bookmaker

            odd_00 = None

            if game['bookmakers']:

                outcomes = game['bookmakers'][0]['markets'][0]['outcomes']

                for o in outcomes:

                    if o['name'] == '0-0':

                        odd_00 = o['price']

                        break

            

            if odd_00:

                results.append({

                    "Tijd": start_time.strftime('%H:%M (%d-%m)'),

                    "Wedstrijd": f"{home} - {away}",

                    "Odd 0-0": odd_00,

                    "RawTime": start_time # Voor het sorteren

                })

        

        # Sorteren op tijd

        df = pd.DataFrame(results).sort_values(by="RawTime")

        return df.drop(columns=['RawTime'])

    

    except Exception as e:

        st.error(f"Fout bij ophalen data: {e}")

        return pd.DataFrame()



if st.button('Ververs Odds'):

    df = get_data()

    if not df.empty:

        st.table(df) # Een strakke tabel zonder poespas

    else:

        st.write("Geen 0-0 odds gevonden op dit moment.")

else:

    st.info("Klik op de knop om de lijst op te halen.")
