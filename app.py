import streamlit as st
import pandas as pd
import requests
import random
from datetime import datetime

# --- CONFIG ---
API_KEY = 'ae33f20cd78d0b2b015703ded3330fcb'
LEAGUES = ["soccer_uefa_champs_league", "soccer_epl", "soccer_spain_la_liga", "soccer_netherlands_eredivisie", "soccer_italy_serie_a", "soccer_germany_bundesliga"]

st.set_page_config(page_title="Pro Punter - Goals Forced", layout="wide")
st.title("⚖️ Pro Punter - Goals & BTTS Prioriteit (25-02)")

def get_data():
    goal_pool = []
    win_pool = []
    today_str = "2026-02-25"
    
    with st.spinner("Zoeken naar Goals en Winst markten..."):
        for league in LEAGUES:
            url = f"https://api.the-odds-api.com/v4/sports/{league}/odds/?apiKey={API_KEY}&regions=eu&markets=h2h,totals,btts&oddsFormat=decimal"
            try:
                r = requests.get(url, timeout=7)
                if r.status_code == 200:
                    data = r.json()
                    for game in data:
                        if today_str in game['commence_time']:
                            if game.get('bookmakers'):
                                bm = game['bookmakers'][0]
                                for m in bm['markets']:
                                    for o in m['outcomes']:
                                        price = o['price']
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

# --- GENERATOR ---
if st.button("🚀 GENEREER SLIPS (GOALS PRIORITEIT)"):
    goal_pool, win_pool = get_data()
    
    if not goal_pool and not win_pool:
        st.error("Niets gevonden.")
    else:
        st.info(f"Pool: {len(goal_pool)} Goal/BTTS opties en {len(win_pool)} Winst opties.")
        
        all_rows = []
        for target in [1.5, 2.0, 3.0, 5.0]:
            # SCHUD DE BAKKEN
            random.shuffle(goal_pool)
            random.shuffle(win_pool)
            
            # GECOMBINEERDE LIJST: GOALS ALTIJD BOVENAAN
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
                        "Tijd": item['Tijd'], "Match": item['Match'],
                        "Keuze": item['Keuze'], "Odd": item['Odd']
                    })
                if current_odd >= target: break
            
            all_rows.extend(slip)
            all_rows.append({k: "" for k in ["Slip", "Tijd", "Match", "Keuze", "Odd"]})
            
        st.table(pd.DataFrame(all_rows))
