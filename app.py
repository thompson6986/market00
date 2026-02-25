import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import itertools

# --- CONFIGURATIE ---
st.set_page_config(page_title="Multi-Sport Punter", page_icon="🏀", layout="wide")
API_KEY = 'ae33f20cd78d0b2b015703ded3330fcb'

# --- UITGEBREIDE SPORT LIJST ---
SPORTS = {
    "Voetbal (CL)": "soccer_uefa_champs_league",
    "Voetbal (EPL)": "soccer_epl",
    "Voetbal (Eredivisie)": "soccer_netherlands_eredivisie",
    "Tennis (ATP)": "tennis_atp_dubai", # Voorbeeld toernooi van deze week
    "Tennis (WTA)": "tennis_wta_doha",
    "Basketbal (NBA)": "basketball_nba",
    "Basketbal (EuroLeague)": "basketball_euroleague",
    "IJshockey (NHL)": "icehockey_nhl"
}

st.title("🏆 Multi-Sport Safe Bet Generator")
st.markdown(f"Datum: **Woensdag 25 februari 2026** | Focus: Voetbal, Tennis, Basketbal")

if st.button("🚀 SCAN ALLE SPORTEN VOOR VANDAAG"):
    all_valid_matches = []
    vandaag_str = "2026-02-25"
    
    with st.spinner("Wereldwijde markten afzoeken..."):
        for sport_name, key in SPORTS.items():
            url = f"https://api.the-odds-api.com/v4/sports/{key}/odds/"
            params = {'apiKey': API_KEY, 'regions': 'eu', 'markets': 'h2h,totals', 'oddsFormat': 'decimal'}
            
            try:
                r = requests.get(url, params=params)
                if r.status_code == 200:
                    data = r.json()
                    for game in data:
                        if vandaag_str in game['commence_time']:
                            tijd = datetime.fromisoformat(game['commence_time'].replace('Z', '')).strftime('%H:%M')
                            if game['bookmakers']:
                                bm = game['bookmakers'][0]
                                for market in bm['markets']:
                                    # LOGICA VOOR H2H (Tennis/Voetbal/Basketbal favorieten)
                                    if market['key'] == 'h2h':
                                        for outcome in market['outcomes']:
                                            price = outcome['price']
                                            if 1.12 <= price <= 1.40:
                                                all_valid_matches.append({
                                                    "Tijd": tijd,
                                                    "Match": f"{outcome['name']} (Winst)",
                                                    "Odd": price,
                                                    "Sport": sport_name
                                                })
                                    # LOGICA VOOR TOTALS (Voetbal Over 1.5 / Basketbal Safe Lines)
                                    if market['key'] == 'totals':
                                        for outcome in market['outcomes']:
                                            if (outcome['name'] == 'Over' and outcome['point'] <= 1.5) or \
                                               (sport_name.startswith("Basketbal") and outcome['name'] == 'Over' and outcome['point'] < 210):
                                                price = outcome['price']
                                                if 1.12 <= price <= 1.40:
                                                    all_valid_matches.append({
                                                        "Tijd": tijd,
                                                        "Match": f"{game['home_team']} - {game['away_team']} (Over {outcome['point']})",
                                                        "Odd": price,
                                                        "Sport": sport_name
                                                    })
            except: continue

    if all_valid_matches:
        df = pd.DataFrame(all_valid_matches).drop_duplicates(subset=['Match'])
        st.success(f"Totaal {len(df)} veilige kansen gevonden over alle sporten!")
        st.dataframe(df.sort_values(by="Tijd"), use_container_width=True, hide_index=True)

        # --- DE 4 BETSLIPS ---
        st.divider()
        st.subheader("📑 Professionele Multi-Sport Slips (1.5, 2.0, 3.0, 5.0)")
        targets = [1.5, 2.0, 3.0, 5.0]
        match_pool = df.to_dict('records')
        cols = st.columns(4)

        for idx, target in enumerate(targets):
            with cols[idx]:
                st.info(f"Doel: Odd {target}")
                best_combo = None
                closest_diff = 999
                for r in range(2, 5): # Max 4 games per slip voor veiligheid
                    for combo in itertools.combinations(match_pool, r):
                        total_odd = 1.0
                        for m in combo: total_odd *= m['Odd']
                        diff = abs(total_odd - target)
                        if total_odd >= target and diff < closest_diff and total_odd <= (target * 1.25):
                            closest_diff = diff
                            best_combo = combo
                            final_odd = total_odd
                
                if best_combo:
                    for m in best_combo:
                        st.write(f"🏷️ {m['Sport']}: {m['Match']} ({m['Odd']})")
                    st.success(f"**Totaal: {round(final_odd, 2)}**")
                else:
                    st.write("Niet genoeg matches voor deze odd.")
    else:
        st.error("Nog steeds weinig resultaten. Tip: De NBA en Tennis markten laden vaak pas rond 14:00 - 15:00 uur volledig in.")
