import streamlit as st
import pandas as pd
import requests
import re
from datetime import datetime

# --- 1. CONFIGURATIE ---
st.set_page_config(page_title="Correct Score Database", page_icon="⚽", layout="wide")

# Jouw API Key
API_KEY = 'ae33f20cd78d0b2b015703ded3330fcb'

# Initialiseer archief in sessie (Kolommen gericht op data-analyse)
if 'archief' not in st.session_state:
    st.session_state.archief = pd.DataFrame(columns=["Datum_Tijd", "Competitie", "Wedstrijd", "Odd_00", "Bron"])

if 'temp_data' not in st.session_state:
    st.session_state.temp_data = None

st.title("⚽ 0-0 Correct Score Collector")
st.caption("Focus: Data verzamelen voor latere analyse")

# --- 2. SIDEBAR: DATA BEHEER ---
with st.sidebar:
    st.header("📂 Data Beheer")
    if not st.session_state.archief.empty:
        st.write(f"Aantal records: **{len(st.session_state.archief)}**")
        
        # CSV Export knop
        csv = st.session_state.archief.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Database (CSV)", csv, f"00_data_{datetime.now().strftime('%d-%m')}.csv", "text/csv")
        
        st.divider()
        if st.button("🗑️ Wis Huidig Archief"):
            st.session_state.archief = pd.DataFrame(columns=["Datum_Tijd", "Competitie", "Wedstrijd", "Odd_00", "Bron"])
            st.rerun()

# --- 3. INPUT MODUS ---
tab1, tab2 = st.tabs(["🚀 API Scan", "📋 OddsPortal / Handmatige Invoer"])

with tab1:
    league_key = st.selectbox("Kies League:", ["soccer_uefa_champs_league", "soccer_epl", "soccer_netherlands_eredivisie", "soccer_belgium_first_division", "soccer_spain_la_liga"])
    if st.button("Haal 0-0 Odds op"):
        url = f"https://api.the-odds-api.com/v4/sports/{league_key}/odds/?apiKey={API_KEY}&regions=eu&markets=correct_score"
        r = requests.get(url)
        if r.status_code == 200:
            data = r.json()
            api_list = []
            for game in data:
                time = datetime.fromisoformat(game['commence_time'].replace('Z', '')).strftime('%d-%m %H:%M')
                odd_00 = "N/A"
                if game['bookmakers']:
                    for m in game['bookmakers'][0]['markets']:
                        for o in m['outcomes']:
                            if o['name'] == '0-0': odd_00 = o['price']
                api_list.append({"Tijd": time, "Match": f"{game['home_team']} - {game['away_team']}", "Odd": odd_00, "Comp": league_key})
            st.session_state.temp_data = pd.DataFrame(api_list)
        else:
            st.error("API Fout (422 of Limiet). Gebruik Tab 2.")

with tab2:
    manual_comp = st.text_input("Competitie Naam:", "Champions League")
    plak_veld = st.text_area("Plak OddsPortal data of typ handmatig de odd:", height=100)
    if st.button("Analyseer / Bereid voor"):
        found_odds = re.findall(r'\b\d{1,2}\.\d{2}\b', plak_veld)
        odd_to_use = max([float(o) for o in found_odds]) if found_odds else 0.00
        st.session_state.temp_data = pd.DataFrame([{"Tijd": datetime.now().strftime("%d-%m %H:%M"), "Match": "", "Odd": odd_00, "Comp": manual_comp}])

# --- 4. BEVESTIGEN EN OPSLAAN (HIER GEEF JE DE NAAM) ---
if st.session_state.temp_data is not None:
    st.divider()
    st.subheader("📝 Controleer en voeg toe aan Database")
    
    # We tonen een formulier om de data perfect te maken
    for index, row in st.session_state.temp_data.iterrows():
        with st.expander(f"Data voor: {row['Match'] if row['Match'] else 'Nieuwe Wedstrijd'}", expanded=True):
            c1, c2, c3 = st.columns([2, 1, 1])
            with c1:
                final_name = st.text_input(f"Naam Wedstrijd #{index}", value=row['Match'], key=f"name_{index}")
            with c2:
                final_odd = st.number_input(f"Odd 0-0 #{index}", value=float(row['Odd']) if row['Odd'] != "N/A" else 0.00, step=0.01, key=f"odd_{index}")
            with c3:
                if st.button(f"Opslaan in Database #{index}", key=f"btn_{index}"):
                    new_row = {
                        "Datum_Tijd": row['Tijd'],
                        "Competitie": row['Comp'],
                        "Wedstrijd": final_name,
                        "Odd_00": final_odd,
                        "Bron": "API" if "soccer" in row['Comp'] else "Handmatig"
                    }
                    st.session_state.archief = pd.concat([st.session_state.archief, pd.DataFrame([new_row])], ignore_index=True)
                    st.success(f"Opgeslagen: {final_name}")

# --- 5. HET ARCHIEF ---
st.divider()
st.subheader("📊 Huidige Database (Klaar voor CSV)")
st.dataframe(st.session_state.archief, use_container_width=True, hide_index=True)
