import streamlit as st
import pandas as pd
import requests
import random
from datetime import datetime, timezone

# --- CONFIG ---
API_KEY = 'ae33f20cd78d0b2b015703ded3330fcb'
# Belangrijke competities voor vanavond
LEAGUES = ["soccer_uefa_champs_league", "soccer_epl", "soccer_spain_la_liga", "soccer_netherlands_eredivisie", "basketball_nba"]

st.set_page_config(page_title="Pro Punter - Correcte Datum", layout="wide")
st.title("⚖️ Pro Punter - Strikt Vandaag (25-02)")

def get_clean_today_data():
    results = []
    # De huidige datum vaststellen
    today_str = "2026-02-25"
    tomorrow_str = "2026-02-26" # Voor NBA in de nacht
    
    with st.spinner("Scannen op wedstrijden van vandaag..."):
        for league in LEAGUES:
            url = f"https://api.the-odds-api.com/v4/sports/{league}/odds/?apiKey={API_KEY}&regions=eu&markets=h2h,totals&oddsFormat=decimal"
            try:
                r = requests.get(url, timeout=7)
                if r.status_code == 200:
                    data = r.json()
                    for game in data:
                        commence_time = game['commence_time'] # Formaat: 2026-02-25T20:00:00Z
                        
                        # STRIKTE DATUM CHECK
                        if today_str in commence_time or (tomorrow_str in commence_time and "05:00" > commence_time.split('T')[1]):
                            if game.get('bookmakers'):
                                bm = game['bookmakers'][0]
                                for m in bm['markets']:
                                    for o in m['outcomes']:
                                        price = o['price']
                                        # Professional Safe Range
                                        if 1.10 <= price <= 1.60:
                                            # Labeling
                                            m_type = "GOALS" if m['key'] == 'totals' else "WINNAAR"
                                            results.append({
                                                "Datum": "25-02",
                                                "Tijd": datetime.fromisoformat(commence_time.replace('Z', '+00:00')).strftime("%H:%M"),
                                                "Match": f"{game['home_team']} - {game['away_team']}",
                                                "Keuze": f"{m_type}: {o['name']} {o.get('point','')}",
                                                "Odd": price,
                                                "Priority": 1 if m_type == "GOALS" else 2
                                            })
            except: continue
    return results

# --- GENERATOR ---
if st.button("🚀 GENEREER SLIPS VOOR VANDAAG"):
    data = get_clean_today_data()
    
    if not data:
        st.error("Geen wedstrijden gevonden voor vandaag binnen de safe-range.")
    else:
        # Sorteer: Goals eerst
        data.sort(key=lambda x: x['Priority'])
        
        st.success(f"Gevonden: {len(data)} opties voor vandaag/vannacht.")
        
        all_rows = []
        for target in [1.5, 2.0, 3.0, 5.0]:
            random.shuffle(data)
            current_odd = 1.0
            slip = []
            used_matches = set()
            
            for item in data:
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
            
            all_rows.extend(slip)
            all_rows.append({k: "" for k in ["Slip", "Tijd", "Match", "Keuze", "Odd"]})
            
        st.table(pd.DataFrame(all_rows))
        
        # Download link
        csv = pd.DataFrame(all_rows).to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download CSV voor Sheets", csv, "bets_25_02.csv", "text/csv")
