import streamlit as st
import pandas as pd
import requests
import random
from datetime import datetime

# --- VERVANG DEZE SLEUTEL VOOR DATA ---
API_KEY = 'ae33f20cd78d0b2b015703ded3330fcb' 

st.set_page_config(page_title="Pro Punter - Fresh Start", layout="wide")
st.title("⚖️ Pro Punter - Goals & Slips (Nieuwe Sessie)")

# We gebruiken 'upcoming' om alle sporten in 1x te laden (bespaart enorm veel credits!)
def get_data_efficient():
    goal_pool = []
    win_pool = []
    # We scannen de komende 10 uur voor de avond-matchen
    url = f"https://api.the-odds-api.com/v4/sports/upcoming/odds/?apiKey={API_KEY}&regions=eu&markets=h2h,totals,btts&oddsFormat=decimal"
    
    try:
        r = requests.get(url, timeout=10)
        # Check credits in de header
        rem = r.headers.get('x-requests-remaining', '0')
        st.sidebar.metric("Resterende Credits", rem)
        
        if r.status_code != 200:
            return None, None
            
        data = r.json()
        for game in data:
            if game.get('bookmakers'):
                bm = game['bookmakers'][0]
                for m in bm['markets']:
                    for o in m['outcomes']:
                        price = o['price']
                        # Jouw professionele range
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
                                item["Keuze"] = f"WINST: {o['name']}"
                                win_pool.append(item)
        return goal_pool, win_pool
    except:
        return None, None

# --- UI ---
if st.button("🚀 GENEREER NU ALLES VOOR VANAVOND"):
    goals, wins = get_data_efficient()
    
    if not goals and not wins:
        st.error("API limiet bereikt of geen verbinding. Voer een nieuwe API-key in.")
    else:
        st.success(f"Gelukt! {len(goals)} Goal-opties en {len(wins)} Winst-opties gevonden.")
        
        all_slips = []
        for target in [1.5, 2.0, 3.0, 5.0]:
            random.shuffle(goals)
            random.shuffle(wins)
            # Dwing goals als eerste keuze
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
            all_slips.append({k: "" for k in ["Slip", "Tijd", "Match", "Keuze", "Odd"]})
            
        st.table(pd.DataFrame(all_slips))
