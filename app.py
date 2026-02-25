import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timezone, timedelta
import random

# --- CONFIG ---
st.set_page_config(page_title="Pro Punter - Goal Focus", layout="wide")
API_KEY = 'ae33f20cd78d0b2b015703ded3330fcb'

st.title("⚖️ Pro Punter - Goals & Totals (25-02)")
st.sidebar.write("🎯 Focus: Over 1.5, Over 2.5 & Winnaar")

TARGET_LEAGUES = [
    "soccer_uefa_champs_league", "soccer_epl", "soccer_spain_la_liga", 
    "soccer_italy_serie_a", "soccer_netherlands_eredivisie", "basketball_nba"
]

def get_goal_markets():
    all_data = []
    now = datetime.now(timezone.utc)
    hard_stop = datetime(2026, 2, 26, 6, 0, tzinfo=timezone.utc)
    
    with st.spinner("Scannen op Over/Under en Favorieten..."):
        for league in TARGET_LEAGUES:
            url = f"https://api.the-odds-api.com/v4/sports/{league}/odds/"
            # We vragen expliciet 'totals' en 'h2h' op
            params = {
                'apiKey': API_KEY, 'regions': 'eu', 
                'markets': 'h2h,totals', 'oddsFormat': 'decimal'
            }
            try:
                r = requests.get(url, params=params)
                if r.status_code == 200:
                    games = r.json()
                    for g in games:
                        m_time = datetime.fromisoformat(g['commence_time'].replace('Z', '+00:00'))
                        
                        if now < m_time < hard_stop:
                            if g.get('bookmakers'):
                                bm = g['bookmakers'][0]
                                for market in bm['markets']:
                                    for o in market['outcomes']:
                                        price = o['price']
                                        
                                        # Filter op jouw Safe Range (1.10 - 1.55)
                                        if 1.10 <= price <= 1.55:
                                            m_label = ""
                                            if market['key'] == 'h2h':
                                                m_label = f"Winst: {o['name']}"
                                            elif market['key'] == 'totals':
                                                # Maak het label duidelijk: bijv. "Over 1.5 Goals"
                                                m_label = f"Goals: {o['name']} {o.get('point','')}"
                                            
                                            all_data.append({
                                                "League": league.split('_')[-1].upper(),
                                                "Tijd": m_time.strftime("%H:%M"),
                                                "Match": f"{g['home_team']} - {g['away_team']}",
                                                "Keuze": m_label,
                                                "Odd": price
                                            })
            except: continue
    return all_data

# --- UI ---
if st.button("🚀 GENEREER SLIPS (INCLUSIEF GOALS)"):
    data = get_goal_markets()
    
    if data:
        # Sorteer zodat je eerst 'Goals' ziet in de lijst (optioneel)
        data.sort(key=lambda x: "Goals" not in x['Keuze'])
        
        st.success(f"Gevonden: {len(data)} kansen (incl. Under/Over)!")
        
        final_rows = []
        for target in [1.5, 2.0, 3.0, 5.0]:
            random.shuffle(data)
            current_odd = 1.0
            slip_items = []
            
            # Probeer een slip te bouwen met minstens 1 Goal markt voor de variatie
            for item in data:
                if current_odd < target:
                    current_odd *= item['Odd']
                    slip_items.append({
                        "Slip": f"Target {target} (@{round(current_odd, 2)})",
                        "Tijd": item['Tijd'], 
                        "Match": f"[{item['League']}] {item['Match']}", 
                        "Keuze": item['Keuze'], "Odd": item['Odd']
                    })
                else: break
            
            if slip_items:
                final_rows.extend(slip_items)
                final_rows.append({k: "" for k in ["Slip", "Tijd", "Match", "Keuze", "Odd"]})
            
        df = pd.DataFrame(final_rows)
        st.table(df)
        
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 DOWNLOAD CSV", csv, "pro_goals_bets.csv", "text/csv")
    else:
        st.error("Geen data gevonden. De API heeft voor deze markten momenteel geen odds in de safe-range.")
