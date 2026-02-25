import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timezone, timedelta
import random

# --- CONFIG ---
st.set_page_config(page_title="Pro Punter V6", layout="wide")
API_KEY = 'ae33f20cd78d0b2b015703ded3330fcb'

st.title("⚖️ Professional Punter Dashboard")

# De meest stabiele sport-keys van dit moment
LEAGUES = [
    "soccer_uefa_champs_league", "soccer_epl", "soccer_spain_la_liga", 
    "soccer_italy_serie_a", "soccer_germany_bundesliga", "basketball_nba"
]

# --- FUNCTIE: ALLES IN ÉÉN ---
def get_bets_and_build_slips():
    all_data = []
    # 1. HAAL DATA OP
    for league in LEAGUES:
        url = f"https://api.the-odds-api.com/v4/sports/{league}/odds/"
        params = {'apiKey': API_KEY, 'regions': 'eu', 'markets': 'h2h,totals,btts', 'oddsFormat': 'decimal'}
        try:
            r = requests.get(url, params=params)
            if r.status_code == 200:
                games = r.json()
                for g in games:
                    if g.get('bookmakers'):
                        bm = g['bookmakers'][0]
                        for m in bm['markets']:
                            for o in m['outcomes']:
                                if 1.10 <= o['price'] <= 1.70:
                                    all_data.append({
                                        "Tijd": datetime.fromisoformat(g['commence_time'].replace('Z', '+00:00')).strftime("%H:%M"),
                                        "Match": f"{g['home_team']} - {g['away_team']}",
                                        "Keuze": o['name'],
                                        "Odd": o['price']
                                    })
        except: continue
    
    if not all_data:
        return None

    # 2. BOUW SLIPS (Targets: 1.5, 2, 3, 5)
    final_slips = []
    for target in [1.5, 2.0, 3.0, 5.0]:
        random.shuffle(all_data)
        current_odd = 1.0
        current_slip = []
        
        for item in all_data:
            if current_odd < target:
                current_odd *= item['Odd']
                current_slip.append({
                    "Slip": f"Target {target} (@{round(current_odd, 2)})",
                    "Tijd": item['Tijd'], "Match": item['Match'], "Keuze": item['Keuze'], "Odd": item['Odd']
                })
            if current_odd >= target: break
        
        final_slips.extend(current_slip)
        final_slips.append({k: "" for k in ["Slip", "Tijd", "Match", "Keuze", "Odd"]}) # Witregel
        
    return pd.DataFrame(final_slips)

# --- UI ---
if st.button("🚀 GENEREER MIJN DAGELIJKSE BETSLIPS"):
    result_df = get_bets_and_build_slips()
    
    if result_df is not None:
        st.success("Slips succesvol gegenereerd!")
        st.table(result_df)
        
        csv = result_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 DOWNLOAD VOOR GOOGLE SHEETS", csv, "pro_bets.csv", "text/csv")
    else:
        st.error("Kon geen data ophalen. Is je API Key nog geldig?")

st.info("Deze knop doet alles: Scannen, filteren en slips bouwen in 1 klik.")
