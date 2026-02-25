import streamlit as st
import pandas as pd
import requests
import random
from datetime import datetime, timedelta

# --- CONFIG ---
API_KEY = 'ae33f20cd78d0b2b015703ded3330fcb'
# Ruime lijst van sporten om data te garanderen
LEAGUES = [
    "soccer_uefa_champs_league", "soccer_epl", "soccer_spain_la_liga", 
    "soccer_italy_serie_a", "soccer_germany_bundesliga", "soccer_netherlands_eredivisie",
    "soccer_portugal_primeira_liga", "soccer_belgium_first_division"
]

st.set_page_config(page_title="Pro Punter - Goal Fix", layout="wide")
st.title("⚖️ Pro Punter - Goals & BTTS (Vanavond 25-02)")

def get_data():
    goal_pool = []
    win_pool = []
    # We kijken naar alles wat vandaag begint
    today_date = datetime.now().strftime("%Y-%m-%d")
    
    with st.spinner("Data ophalen van alle Europese competities..."):
        for league in LEAGUES:
            url = f"https://api.the-odds-api.com/v4/sports/{league}/odds/?apiKey={API_KEY}&regions=eu&markets=h2h,totals,btts&oddsFormat=decimal"
            try:
                r = requests.get(url, timeout=10)
                if r.status_code == 200:
                    data = r.json()
                    for game in data:
                        # Ruime check: zit de datum van vandaag in de starttijd?
                        if today_date in game['commence_time']:
                            if game.get('bookmakers'):
                                bm = game['bookmakers'][0]
                                for m in bm['markets']:
                                    for o in m['outcomes']:
                                        price = o['price']
                                        # Jouw safe-range (1.10 - 1.65)
                                        if 1.10 <= price <= 1.65:
                                            item = {
                                                "Tijd": datetime.fromisoformat(game['commence_time'].replace('Z', '+00:00')).strftime("%H:%M"),
                                                "Match": f"{game['home_team']} - {game['away_team']}",
                                                "Odd": price
                                            }
                                            if m['key'] == 'totals':
                                                item["Keuze"] = f"GOALS: {o['name']} {o.get('point','')}"
                                                goal_pool.append(item)
                                            elif m['key'] == 'btts':
                                                item["Keuze"] = f"BTTS: {o['name']}"
                                                goal_pool.append(item)
                                            elif m['key'] == 'h2h':
                                                item["Keuze"] = f"WINNAAR: {o['name']}"
                                                win_pool.append(item)
            except: continue
    return goal_pool, win_pool

# --- UI ---
if st.button("🚀 GENEREER SLIPS (Dwing Goals)"):
    goal_pool, win_pool = get_data()
    
    if not goal_pool and not win_pool:
        st.error("Nog steeds niets gevonden. Mogelijk is de API-key limiet voor vandaag bereikt (check de credits in de vorige versie).")
    else:
        st.info(f"Gevonden: {len(goal_pool)} Goals/BTTS opties en {len(win_pool)} Winnaar opties.")
        
        all_rows = []
        for target in [1.5, 2.0, 3.0, 5.0]:
            random.shuffle(goal_pool)
            random.shuffle(win_pool)
            
            # Belangrijk: We zetten GOALS vooraan in de lijst
            combined_pool = goal_pool + win_pool
            
            current_odd = 1.0
            slip = []
            used_matches = set()
            
            for item in combined_pool:
                if current_odd < target and item['Match'] not in used_matches:
                    current_odd *= item['Odd']
                    used_matches.add(item['Match'])
                    slip.append({
                        "Slip": f"Target {target} (@{round(current_odd, 2)})",
                        "Tijd": item['Tijd'],
                        "Match": item['Match'],
                        "Keuze": item['Keuze'],
                        "Odd": item['Odd']
                    })
                if current_odd >= target: break
            
            if slip:
                all_rows.extend(slip)
                all_rows.append({k: "" for k in ["Slip", "Tijd", "Match", "Keuze", "Odd"]})
            
        if all_rows:
            st.table(pd.DataFrame(all_rows))
        else:
            st.warning("Kon geen combinaties maken met de huidige odds.")
