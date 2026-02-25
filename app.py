import streamlit as st
import pandas as pd
import requests
import re
from datetime import datetime

# --- 1. CONFIGURATIE ---
st.set_page_config(page_title="0-0 Data Collector", page_icon="⚽", layout="wide")

# Jouw API Key
API_KEY = 'ae33f20cd78d0b2b015703ded3330fcb'

# Initialiseer sessie variabelen
if 'archief' not in st.session_state:
    st.session_state.archief = pd.DataFrame(columns=["Datum_Tijd", "Competitie", "Wedstrijd", "Odd_00"])

if 'temp_data' not in st.session_state:
    st.session_state.temp_data = None

st.title("⚽ 0-0 Correct Score Database")
st.caption("Verzamel 0-0 data voor latere analyse")

# --- 2. SIDEBAR: DATA BEHEER ---
with st.sidebar:
    st.header("📂 Export & Beheer")
    if not st.session_state.archief.empty:
        st.write(f"Totaal aantal rijen: **{len(st.session_state.archief)}**")
        
        # CSV Export
        csv = st.session_state.archief.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download CSV Bestand", csv, f"00_database_{datetime.now().strftime('%d-%m')}.csv", "text/csv")
        
        st.divider()
        if st.button("🗑️ Wis Archief"):
            st.session_state.archief = pd.DataFrame(columns=["Datum_Tijd", "Competitie", "Wedstrijd", "Odd_00"])
            st.rerun()

# --- 3. INPUT MODUS ---
tab1, tab2 = st.tabs(["🚀 API Scan (Grote Leagues)", "📋 Handmatige Invoer / OddsPortal"])

with tab1:
    league_key = st.selectbox("Kies League:", ["soccer_uefa_champs_league", "soccer_epl", "soccer_netherlands_eredivisie", "soccer_belgium_first_division", "soccer_spain_la_liga"])
    if st.button("Scan API"):
        url = f"https://api.the-odds-api.com/v4/sports/{league_key}/odds/?apiKey={API_KEY}&regions=eu&markets=correct_score"
        try:
            r = requests.get(url)
            if r.status_code == 200:
                data = r.json()
                api_list = []
                for game in data:
                    time = datetime.fromisoformat(game['commence_time'].replace('Z', '')).strftime('%d-%m %H:%M')
                    best_odd = 0.00
                    if game['bookmakers']:
                        for m in game['bookmakers'][0]['markets']:
                            for o in m['outcomes']:
                                if o['name'] == '0-0': best_odd = o['price']
                    api_list.append({"Tijd": time, "Match": f"{game['home_team']} - {game['away_team']}", "Odd": best_odd, "Comp": league_key})
                st.session_state.temp_data = pd.DataFrame(api_list)
            else:
                st.error("API Error 422 of Limiet. Gebruik de handmatige tab.")
        except:
            st.error("Verbindingsfout.")

with tab2:
    manual_comp = st.text_input("Competitie:", "Champions League")
    plak_veld = st.text_area("Plak hier tekst met een odd (bijv. van OddsPortal):", height=100)
    if st.button("Bereid Handmatige Invoer voor"):
        # Zoek naar getallen zoals 7.50 of 12.00
        found_odds = re.findall(r'\b\d{1,2}\.\d{2}\b', plak_veld)
        odd_to_use = float(max(found_odds)) if found_odds else 0.00
        
        # Hier zat de fout: we gebruiken nu 'odd_to_use'
        st.session_state.temp_data = pd.DataFrame([{
            "Tijd": datetime.now().strftime("%d-%m %H:%M"), 
            "Match": "", 
            "Odd": odd_to_use, 
            "Comp": manual_comp
        }])

# --- 4. DATA BEWERKEN EN OPSLAAN ---
if st.session_state.temp_data is not None:
    st.divider()
    st.subheader("📝 Controleer en Sla Op")
    
    for index, row in st.session_state.temp_data.iterrows():
        # Elke gevonden match krijgt zijn eigen invoerveld
        with st.container():
            c1, c2, c3 = st.columns([2, 1, 1])
            with c1:
                input_name = st.text_input(f"Naam Wedstrijd", value=row['Match'], key=f"n_{index}")
            with c2:
                input_odd = st.number_input(f"Odd 0-0", value=float(row['Odd']), step=0.01, key=f"o_{index}")
            with c3:
                st.write("") # Uitlijning
                if st.button(f"✅ Sla op", key=f"b_{index}"):
                    new_entry = {
                        "Datum_Tijd": row['Tijd'],
                        "Competitie": row['Comp'],
                        "Wedstrijd": input_name,
                        "Odd_00": input_odd
                    }
                    st.session_state.archief = pd.concat([st.session_state.archief, pd.DataFrame([new_entry])], ignore_index=True)
                    st.toast(f"Opgeslagen: {input_name}")

# --- 5. HET ARCHIEF ---
st.divider()
st.subheader("📊 Je Database Overzicht")
if not st.session_state.archief.empty:
    st.dataframe(st.session_state.archief, use_container_width=True, hide_index=True)
else:
    st.info("De database is nog leeg.")
