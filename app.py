import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timezone
import random

# --- CONFIG ---
st.set_page_config(page_title="Pro Punter - Evening Edition", layout="wide")
API_KEY = 'ae33f20cd78d0b2b015703ded3330fcb'

st.title("⚖️ Professional Punter - Evening Session")
st.info("Scanner gericht op de wedstrijden van vanavond (Champions League & NBA).")

def get_evening_bets():
    # We focussen op voetbal voor vanavond (vanaf 18:00 UTC)
    # Dit dwingt de API om verder te kijken dan de huidige live matchen
    url = f"https://api.the-odds-api.com/v4/sports/upcoming/odds/"
    params = {
        'apiKey': API_KEY,
        'regions': 'eu',
        'markets': 'h2h,totals,btts',
        'oddsFormat': 'decimal'
    }
    
    try:
        r = requests.get(url, params=params)
        
        # CREDITS TONEN IN SIDEBAR
        rem = r.headers.get('x-requests-remaining', 'Niet gevonden')
        used = r.headers.get('x-requests-used', '0')
        with st.sidebar:
            st.metric("Resterende Credits", rem)
            st.write(f"Vandaag verbruikt: {used}")

        if r.status_code != 200:
            st.error(f"API Error: {r.status_code}")
            return None

        all_data = []
        games = r.json()
        now = datetime.now(timezone.utc)

        for g in games:
            m_time = datetime.fromisoformat(g['commence_time'].replace('Z', '+00:00'))
            
            # FILTER: Alleen wedstrijden die nog MOETEN beginnen (na nu)
            if m_time > now:
                if g.get('bookmakers'):
                    bm = g['bookmakers'][0]
                    for m in bm['markets']:
                        for o in m['outcomes']:
                            # Jouw pro-range
                            if 1.10 <= o['price'] <= 1.65:
                                label = ""
                                if m['key'] == 'h2h': label = f"Winst: {o['name']}"
                                elif m['key'] == 'btts': label = f"BTTS: {o['name']}"
                                elif m['key'] == 'totals': label = f"Goals: {o['name']} {o.get('point','')}"
                                
                                all_data.append({
                                    "Sport": g['sport_title'],
                                    "Tijd": m_time.strftime("%H:%M"),
                                    "Datum": m_time.strftime("%d-%m"),
                                    "Match": f"{g['home_team']} - {g['away_team']}",
                                    "Keuze": label,
                                    "Odd": o['price']
                                })
        return all_data
    except Exception as e:
        st.error(f"Fout: {e}")
        return None

# --- UI LOGICA ---
if st.button("🚀 SCAN VOOR VANAVOND"):
    data = get_evening_bets()
    
    if data and len(data) > 0:
        st.success(f"Gevonden: {len(data)} opties voor vanavond!")
        
        # BOUW DE 4 SLIPS
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
                        "Datum": item['Datum'], "Tijd": item['Tijd'], 
                        "Match": f"[{item['Sport']}] {item['Match']}", 
                        "Keuze": item['Keuze'], "Odd": item['Odd']
                    })
                else: break
            
            final_rows.extend(slip_items)
            final_rows.append({k: "" for k in ["Slip", "Datum", "Tijd", "Match", "Keuze", "Odd"]})
            
        df = pd.DataFrame(final_rows)
        st.table(df)
        
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 DOWNLOAD CSV", csv, f"bets_avond_25_02.csv", "text/csv")
    else:
        st.warning("Geen toekomstige wedstrijden gevonden in de huidige scan. Probeer de scan over een paar minuten opnieuw.")
