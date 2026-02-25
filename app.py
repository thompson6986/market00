import streamlit as st
import pandas as pd
import requests
import random
from datetime import datetime

# --- CONFIG ---
API_KEY = 'ae33f20cd78d0b2b015703ded3330fcb'
LEAGUES = ["soccer_uefa_champs_league", "soccer_epl", "soccer_spain_la_liga", "soccer_netherlands_eredivisie"]

st.set_page_config(page_title="Pro Fix", layout="wide")
st.title("⚖️ Pro Punter - Direct Scan")

# --- SIMPELE SCANNER ---
def quick_scan():
    results = []
    # We scannen maar 3 leagues tegelijk om snelheid te garanderen
    for league in LEAGUES[:3]:
        url = f"https://api.the-odds-api.com/v4/sports/{league}/odds/?apiKey={API_KEY}&regions=eu&markets=h2h,totals&oddsFormat=decimal"
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                data = r.json()
                for game in data:
                    if game.get('bookmakers'):
                        bm = game['bookmakers'][0]
                        for m in bm['markets']:
                            for o in m['outcomes']:
                                # Ruime filter om ALTIJD iets te vinden
                                if 1.10 <= o['price'] <= 1.80:
                                    results.append({
                                        "Tijd": game['commence_time'],
                                        "Match": f"{game['home_team']} - {game['away_team']}",
                                        "Keuze": f"{m['key']}: {o['name']} {o.get('point','')}",
                                        "Odd": o['price'],
                                        "Type": m['key']
                                    })
        except Exception as e:
            st.warning(f"Fout bij {league}: {e}")
    return results

# --- HOOFDPROGRAMMA ---
if st.button("🚀 START DIRECTE SCAN"):
    raw_data = quick_scan()
    
    if not raw_data:
        st.error("Geen data gevonden. De API reageert niet of de credits zijn op.")
    else:
        st.success(f"Gevonden: {len(raw_data)} opties.")
        
        # Sorteer op Goals eerst (jouw wens)
        raw_data.sort(key=lambda x: x['Type'] != 'totals')
        
        # Maak 4 slips
        all_slips = []
        for target in [1.5, 2.0, 3.0, 5.0]:
            random.shuffle(raw_data)
            current_odd = 1.0
            slip = []
            for item in raw_data:
                if current_odd < target:
                    current_odd *= item['Odd']
                    slip.append({
                        "Slip": f"Target {target} (@{round(current_odd,2)})",
                        "Match": item['Match'],
                        "Keuze": item['Keuze'].replace('totals:', 'GOALS:'),
                        "Odd": item['Odd']
                    })
                else: break
            all_slips.extend(slip)
            all_slips.append({k: "" for k in ["Slip", "Match", "Keuze", "Odd"]})

        st.table(pd.DataFrame(all_slips))
