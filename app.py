import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timezone
import random

# --- CONFIG ---
st.set_page_config(page_title="Pro Goal Focus", layout="wide")
API_KEY = 'ae33f20cd78d0b2b015703ded3330fcb'

st.title("⚖️ Pro Punter - Goals & BTTS Prioriteit")

TARGET_LEAGUES = [
    "soccer_uefa_champs_league", "soccer_epl", "soccer_spain_la_liga", 
    "soccer_italy_serie_a", "soccer_netherlands_eredivisie", "soccer_portugal_primeira_liga"
]

def get_diverse_bets():
    all_data = []
    now = datetime.now(timezone.utc)
    hard_stop = datetime(2026, 2, 26, 6, 0, tzinfo=timezone.utc)
    
    with st.spinner("Scannen op Goals, BTTS en Favorieten..."):
        for league in TARGET_LEAGUES:
            url = f"https://api.the-odds-api.com/v4/sports/{league}/odds/"
            # We dwingen alle drie de markten af
            params = {
                'apiKey': API_KEY, 'regions': 'eu', 
                'markets': 'h2h,totals,btts', 'oddsFormat': 'decimal'
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
                                        
                                        # Professional Safe Range
                                        if 1.10 <= price <= 1.60:
                                            m_label = ""
                                            m_weight = 0 # Prioriteit score
                                            
                                            if market['key'] == 'totals':
                                                m_label = f"Goals: {o['name']} {o.get('point','')}"
                                                m_weight = 3 # Hoogste prioriteit
                                            elif market['key'] == 'btts':
                                                m_label = f"BTTS: {o['name']}"
                                                m_weight = 2
                                            elif market['key'] == 'h2h':
                                                m_label = f"Winst: {o['name']}"
                                                m_weight = 1 # Laagste prioriteit
                                            
                                            all_data.append({
                                                "Weight": m_weight,
                                                "Tijd": m_time.strftime("%H:%M"),
                                                "Match": f"{g['home_team']} - {g['away_team']}",
                                                "Keuze": m_label,
                                                "Odd": price
                                            })
            except: continue
    return all_data

# --- UI ---
if st.button("🚀 GENEREER DIVERSE SLIPS"):
    data = get_diverse_bets()
    
    if data:
        # SORTEER OP PRIORITEIT: Eerst Goals, dan BTTS, dan pas Winst
        data.sort(key=lambda x: x['Weight'], reverse=True)
        
        st.success(f"Totaal {len(data)} opties gevonden. Prioriteit gegeven aan Goal-markten.")
        
        final_rows = []
        for target in [1.5, 2.0, 3.0, 5.0]:
            # We schudden de data niet volledig willekeurig, 
            # maar houden de goal-markten (Weight 3) vaker bovenin.
            pool = [d for d in data if d['Weight'] >= 2] + [d for d in data if d['Weight'] == 1]
            
            current_odd = 1.0
            slip_items = []
            for item in pool:
                if current_odd < target:
                    # Voorkom dubbele match in 1 slip
                    if not any(item['Match'] in s['Match'] for s in slip_items):
                        current_odd *= item['Odd']
                        slip_items.append({
                            "Slip": f"Target {target} (@{round(current_odd, 2)})",
                            "Tijd": item['Tijd'], "Match": item['Match'], 
                            "Keuze": item['Keuze'], "Odd": item['Odd']
                        })
                else: break
            
            final_rows.extend(slip_items)
            final_rows.append({k: "" for k in ["Slip", "Tijd", "Match", "Keuze", "Odd"]})
            
        st.table(pd.DataFrame(final_rows))
