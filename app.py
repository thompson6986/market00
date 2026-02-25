import streamlit as st
import pandas as pd
import requests
import random
from datetime import datetime

# --- CONFIG ---
API_KEY = 'ae33f20cd78d0b2b015703ded3330fcb' 

st.set_page_config(page_title="Pro Punter - Goal Fix", layout="wide")
st.title("⚖️ Pro Punter - Goals & Slips (259 Credits Mode)")

def get_data_split():
    goal_pool = []
    win_pool = []
    
    # 1. Haal eerst de GOALS (totals) op
    url_goals = f"https://api.the-odds-api.com/v4/sports/upcoming/odds/?apiKey={API_KEY}&regions=eu&markets=totals&oddsFormat=decimal"
    # 2. Haal daarna de WINNAARS (h2h) op
    url_wins = f"https://api.the-odds-api.com/v4/sports/upcoming/odds/?apiKey={API_KEY}&regions=eu&markets=h2h&oddsFormat=decimal"
    
    try:
        # GOALS OPHALEN
        r_g = requests.get(url_goals, timeout=10)
        # WINNAARS OPHALEN
        r_w = requests.get(url_wins, timeout=10)
        
        # Credit check uit de header
        rem = r_g.headers.get('x-requests-remaining', '259')
        st.sidebar.metric("Resterende Credits", rem)

        if r_g.status_code == 200:
            for game in r_g.json():
                if game.get('bookmakers'):
                    for m in game['bookmakers'][0]['markets']:
                        for o in m['outcomes']:
                            if 1.10 <= o['price'] <= 1.60:
                                goal_pool.append({
                                    "Tijd": datetime.fromisoformat(game['commence_time'].replace('Z', '+00:00')).strftime("%H:%M"),
                                    "Match": f"{game['home_team']} - {game['away_team']}",
                                    "Keuze": f"GOALS: {o['name']} {o.get('point','')}",
                                    "Odd": o['price'],
                                    "Type": "GOAL"
                                })

        if r_w.status_code == 200:
            for game in r_w.json():
                if game.get('bookmakers'):
                    for m in game['bookmakers'][0]['markets']:
                        for o in m['outcomes']:
                            if 1.10 <= o['price'] <= 1.50:
                                win_pool.append({
                                    "Tijd": datetime.fromisoformat(game['commence_time'].replace('Z', '+00:00')).strftime("%H:%M"),
                                    "Match": f"{game['home_team']} - {game['away_team']}",
                                    "Keuze": f"WINST: {o['name']}",
                                    "Odd": o['price'],
                                    "Type": "WIN"
                                })
        return goal_pool, win_pool
    except:
        return [], []

# --- UI ---
if st.button("🚀 GENEREER SLIPS (GEFORCEERDE GOALS)"):
    goals, wins = get_data_split()
    
    if not goals and not wins:
        st.error("Kon geen data ophalen. Check je internet of API key.")
    else:
        st.success(f"Gevonden: {len(goals)} Goal-opties en {len(wins)} Winst-opties.")
        
        all_slips = []
        for target in [1.5, 2.0, 3.0, 5.0]:
            random.shuffle(goals)
            random.shuffle(wins)
            # Dwing de generator om EERST alle goals te gebruiken
            pool = goals + wins
            
            current_odd = 1.0
            slip = []
            used_matches = set()
            
            for item in pool:
                if current_odd < target and item['Match'] not in used_matches:
                    current_odd *= item['Odd']
                    used_matches.add(item['Match'])
                    slip.append({
                        "Slip": f"Target {target} (@{round(current_odd, 2)})",
                        "Tijd": item['Tijd'], "Match": item['Match'], "Keuze": item['Keuze'], "Odd": item['Odd']
                    })
                if current_odd >= target: break
            
            all_slips.extend(slip)
            all_rows = pd.DataFrame(all_slips) if all_slips else pd.DataFrame()
            # Witregel toevoegen voor overzicht
            all_slips.append({k: "" for k in ["Slip", "Tijd", "Match", "Keuze", "Odd"]})
            
        st.table(pd.DataFrame(all_slips))
