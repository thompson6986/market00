import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import itertools

# --- 1. CONFIGURATIE ---
st.set_page_config(page_title="Pro Punter Dashboard", page_icon="⚖️", layout="wide")
API_KEY = 'ae33f20cd78d0b2b015703ded3330fcb'

# Initialiseer de database in de sessie
if 'bet_history' not in st.session_state:
    st.session_state.bet_history = pd.DataFrame(columns=["Datum", "Slip_Type", "Wedstrijden", "Totale_Odd", "Status"])

st.title("⚖️ Professional Betting & Audit System")
st.markdown(f"**Handelsdag:** Woensdag 25 februari 2026 | **Systeemstatus:** Live Monitoring")

# --- 2. MULTI-SPORT SCANNER ---
SPORTS = {
    "Voetbal (Global)": "soccer", 
    "Tennis (ATP/WTA)": "tennis",
    "Basketbal (NBA/EU)": "basketball",
    "IJshockey (NHL)": "icehockey"
}

with st.expander("🔍 Scanner Instellingen", expanded=True):
    selected_sports = st.multiselect("Selecteer markten voor analyse:", list(SPORTS.keys()), default=list(SPORTS.keys()))
    scan_btn = st.button("🚀 START MARKTANALYSE")

all_valid_matches = []
if scan_btn:
    vandaag_str = "2026-02-25"
    with st.spinner("Data-mining wereldwijde sportmarkten..."):
        # We halen eerst alle actieve competities op voor de geselecteerde sporten
        all_leagues_url = f"https://api.the-odds-api.com/v4/sports/?apiKey={API_KEY}"
        leagues_data = requests.get(all_leagues_url).json()
        
        target_keys = [l['key'] for l in leagues_data if any(s.split(' ')[0].lower() in l['key'].lower() for s in selected_sports)]

        for key in target_keys[:15]: # Limiet om API-credits te sparen
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
                                for market in game['bookmakers'][0]['markets']:
                                    for outcome in market['outcomes']:
                                        price = outcome['price']
                                        # Professional Safe Range: 1.12 - 1.45
                                        if 1.12 <= price <= 1.45:
                                            # Filter voor Totals: enkel safe lines
                                            if market['key'] == 'totals' and outcome['point'] > 2.5 and "soccer" in key: continue 
                                            
                                            label = f"{outcome['name']}" if market['key'] == 'h2h' else f"{outcome['name']} {outcome.get('point', '')}"
                                            all_valid_matches.append({
                                                "Tijd": tijd,
                                                "Match": f"{game['home_team']} vs {game['away_team']}",
                                                "Selectie": label,
                                                "Odd": price,
                                                "Sport": game['sport_title']
                                            })
            except: continue

# --- 3. GENERATOR & PRESENTATIE ---
if all_valid_matches:
    df = pd.DataFrame(all_valid_matches).drop_duplicates(subset=['Match', 'Selectie'])
    st.subheader("📊 Gevonden Waarde-Elementen")
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("📑 Gegenereerde Betslips")
    
    targets = [1.5, 2.0, 3.0, 5.0]
    match_pool = df.to_dict('records')
    cols = st.columns(4)

    for idx, target in enumerate(targets):
        with cols[idx]:
            st.markdown(f"""
            <div style="border: 1px solid #ddd; padding: 15px; border-radius: 10px; background-color: #f9f9f9; color: #333">
                <h4 style="margin-top:0">SLIP TARGET {target}</h4>
            """, unsafe_allow_html=True)
            
            best_combo = None
            closest_diff = 999
            for r in range(2, 5):
                for combo in itertools.combinations(match_pool, r):
                    total_odd = 1.0
                    for m in combo: total_odd *= m['Odd']
                    if total_odd >= target and abs(total_odd - target) < closest_diff and total_odd <= (target * 1.3):
                        closest_diff = abs(total_odd - target)
                        best_combo = combo
                        final_odd = total_odd
            
            if best_combo:
                match_str_list = []
                for m in best_combo:
                    st.markdown(f"**{m['Tijd']}** | {m['Match']}<br><small>{m['Selectie']} @ {m['Odd']}</small>", unsafe_allow_html=True)
                    match_str_list.append(f"{m['Match']} ({m['Selectie']})")
                
                st.markdown(f"<h3 style='color: #1e88e5'>Totaal: {round(final_odd, 2)}</h3>", unsafe_allow_html=True)
                
                if st.button(f"💾 Sla Slip {target} op", key=f"save_{target}"):
                    new_entry = {
                        "Datum": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "Slip_Type": f"Target {target}",
                        "Wedstrijden": " | ".join(match_str_list),
                        "Totale_Odd": round(final_odd, 2),
                        "Status": "OPEN"
                    }
                    st.session_state.bet_history = pd.concat([st.session_state.bet_history, pd.DataFrame([new_entry])], ignore_index=True)
                    st.toast(f"Slip {target} gearchiveerd.")
            st.markdown("</div>", unsafe_allow_html=True)

# --- 4. EXPORT & ARCHIEF ---
st.divider()
st.subheader("📂 Professioneel Archief & Export")

if not st.session_state.bet_history.empty:
    # Weergeven als een professionele audit-log
    st.table(st.session_state.bet_history)
    
    c1, c2 = st.columns(2)
    with c1:
        csv = st.session_state.bet_history.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Audit Log (CSV voor Excel)",
            data=csv,
            file_name=f"punter_audit_{datetime.now().strftime('%d_%m_%Y')}.csv",
            mime="text/csv",
        )
    with c2:
        if st.button("🗑️ Wis Archief"):
            st.session_state.bet_history = pd.DataFrame(columns=["Datum", "Slip_Type", "Wedstrijden", "Totale_Odd", "Status"])
            st.rerun()
else:
    st.info("Nog geen betslips opgeslagen voor export.")
