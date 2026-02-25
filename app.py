import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timezone, timedelta
import random

# --- CONFIG ---
st.set_page_config(page_title="Pro Punter - Alleen Vanavond", layout="wide")
API_KEY = 'ae33f20cd78d0b2b015703ded3330fcb'

st.title("⚖️ Pro Punter - Strikt Vanavond (25-02)")
st.sidebar.write(f"💳 Credits: ~320")

# Belangrijke leagues voor vanavond
TARGET_LEAGUES = [
    "soccer_uefa_champs_league", "soccer_epl", "basketball_nba", 
    "soccer_netherlands_eredivisie", "soccer_spain_la_liga", "soccer_portugal_primeira_liga"
]

def get_tonight_only():
    all_data = []
    now = datetime.now(timezone.utc)
    # HARDE STOP: Morgenochtend 06:00 (zodat we de NBA van vannacht nog wel hebben)
    hard_stop = datetime(2026, 2, 26, 6, 0, tzinfo=timezone.utc)
    
    with st.spinner("Alleen wedstrijden voor vanavond en vannacht zoeken..."):
        for league in TARGET_LEAGUES:
            url = f"https://api.the-odds-api.com/v4/sports/{league}/odds/"
            params = {
                'apiKey': API_KEY,
                'regions': 'eu',
                'markets': 'h2h,totals',
                'oddsFormat': 'decimal'
            }
            try:
                r = requests.get(url, params=params)
                if r.status_code == 200:
                    games = r.json()
                    for g in games:
                        m_time = datetime.fromisoformat(g['commence_time'].replace('Z', '+00:00'))
                        
                        # STRIKTE FILTER: Na NU en voor MORGENOCHTEND 06:00
                        if now < m_time < hard_stop:
                            if g.get('bookmakers'):
                                bm = g['bookmakers'][0]
                                for m in bm['markets']:
                                    for o in m['outcomes']:
                                        price = o['price']
                                        # Professional Safe Range
                                        if 1.10 <= price <= 1.55:
                                            label = ""
                                            if m['key'] == 'h2h': label = f"Winst/Scoort: {o['name']}"
                                            else: label = f"Goals: {o['name']} {o.get('point','')}"
                                            
                                            all_data.append({
                                                "League": league.split('_')[-1].upper(),
                                                "Tijd": m_time.strftime("%H:%M"),
                                                "Match": f"{g['home_team']} - {g['away_team']}",
                                                "Keuze": label,
                                                "Odd": price
                                            })
            except: continue
    return all_data

# --- UI ---
if st.button("🚀 GENEREER SLIPS VOOR VANAVOND (STRIKT)"):
    data = get_tonight_only()
    
    if data:
        st.success(f"Gevonden: {len(data)} kansen die ECHT vanavond/vannacht plaatsvinden!")
        
        final_rows = []
        for target in [1.5, 2.0, 3.0, 5.0]:
            random.shuffle(data)
            current_odd = 1.0
            slip_items = []
            
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
        st.download_button("📥 DOWNLOAD CSV", csv, "pro_tonight_only.csv", "text/csv")
    else:
        st.error("Geen wedstrijden meer gevonden voor de rest van de dag. Mogelijk zijn alle relevante matchen al gestart.")
