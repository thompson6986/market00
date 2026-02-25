import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import random

# --- CONFIG ---
st.set_page_config(page_title="Pro Punter V7 - Credit Saver", layout="wide")
API_KEY = 'ae33f20cd78d0b2b015703ded3330fcb'

st.title("⚖️ Professional Punter - Credit Saver Mode")
st.info("Deze versie gebruikt slechts 1 API-credit per scan.")

def get_efficient_bets():
    # We gebruiken 'upcoming' om alle sporten in 1x te laden (bespaart credits!)
    url = f"https://api.the-odds-api.com/v4/sports/upcoming/odds/"
    params = {
        'apiKey': API_KEY,
        'regions': 'eu',
        'markets': 'h2h,totals', # BTTS weggelaten om data-omvang klein te houden
        'oddsFormat': 'decimal'
    }
    
    try:
        r = requests.get(url, params=params)
        
        # Laat headers zien voor controle van je limiet
        remaining = r.headers.get('x-requests-remaining', 'Onbekend')
        st.sidebar.write(f"💳 Resterende Credits: {remaining}")
        
        if r.status_code != 200:
            st.error(f"API Error: {r.status_code}. Mogelijk is je limiet (500/mnd) bereikt.")
            return None

        all_data = []
        games = r.json()
        for g in games:
            if g.get('bookmakers'):
                bm = g['bookmakers'][0]
                for m in bm['markets']:
                    for o in m['outcomes']:
                        # Focus op jouw safe-range
                        if 1.10 <= o['price'] <= 1.65:
                            all_data.append({
                                "Tijd": datetime.fromisoformat(g['commence_time'].replace('Z', '+00:00')).strftime("%H:%M"),
                                "Match": f"{g['home_team']} - {g['away_team']}",
                                "Keuze": o['name'],
                                "Odd": o['price']
                            })
        return all_data
    except Exception as e:
        st.error(f"Verbindingsfout: {e}")
        return None

# --- UI ---
if st.button("🚀 GENEREER BETSLIPS (LOW CREDIT USAGE)"):
    data = get_efficient_bets()
    
    if data:
        st.success(f"Data succesvol geladen! {len(data)} opties gevonden.")
        
        # BOUW DE 4 SLIPS
        final_rows = []
        for target in [1.5, 2.0, 3.0, 5.0]:
            random.shuffle(data)
            current_odd = 1.0
            for item in data:
                if current_odd < target:
                    current_odd *= item['Odd']
                    final_rows.append({
                        "Slip": f"Target {target} (@{round(current_odd, 2)})",
                        "Tijd": item['Tijd'], "Match": item['Match'], "Keuze": item['Keuze'], "Odd": item['Odd']
                    })
                else: break
            final_rows.append({k: "" for k in ["Slip", "Tijd", "Match", "Keuze", "Odd"]}) # Witregel
            
        df = pd.DataFrame(final_rows)
        st.table(df)
        
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 DOWNLOAD CSV", csv, "daily_pro_bets.csv", "text/csv")
    else:
        st.warning("Geen data gevonden. Controleer de sidebar voor je resterende credits.")
