import streamlit as st
import pandas as pd
import requests
import re
from datetime import datetime
import itertools

# --- CONFIGURATIE ---
st.set_page_config(page_title="Over 1.5 Auto-Generator", page_icon="📈", layout="wide")
API_KEY = 'ae33f20cd78d0b2b015703ded3330fcb'

if 'archief' not in st.session_state:
    st.session_state.archief = pd.DataFrame(columns=["Tijd", "Combinatie", "Totale_Odd"])

st.title("📈 Smart Over 1.5 Generator")
st.caption("Doel: Automatisch combinaties maken (1.15-1.40) | Max 2.30 totaal")

# --- BULK INPUT (DE SNELLE MANIER) ---
st.subheader("📋 Stap 1: Plak OddsPortal Data")
st.info("Kopieer de lijst met wedstrijden en odds van OddsPortal en plak ze hieronder. De generator vist de 'Over 1.5' odds er zelf uit.")

raw_data = st.text_area("Plak hier je data:", height=150, placeholder="Ajax - PSV 1.25\nInter - Porto 1.18...")

if st.button("GENEREER SLIPS UIT DATA"):
    # We vissen namen en odds uit de tekst
    # Zoekt naar patronen zoals "Team A - Team B" gevolgd door een getal tussen 1.10 en 1.50
    matches_found = []
    
    # Simpele extractie: zoek naar regels met een '-' en een decimaal getal
    lines = raw_data.split('\n')
    for line in lines:
        odds = re.findall(r'\b1\.\d{2}\b', line) # Zoekt getallen zoals 1.25
        if odds:
            odd = float(odds[0])
            if 1.15 <= odd <= 1.40:
                # Probeer een naam te vinden (alles voor het getal)
                name = re.sub(r'\b1\.\d{2}\b', '', line).strip().strip('-').strip()
                if not name: name = f"Match met odd {odd}"
                matches_found.append({"Match": name, "Odd": odd})

    if len(matches_found) >= 2:
        st.success(f"{len(matches_found)} geschikte wedstrijden gevonden!")
        
        # GENERATOR
        valid_combos = []
        for r in [2, 3]:
            for combo in itertools.combinations(matches_found, r):
                total_odd = 1.0
                for m in combo: total_odd *= m['Odd']
                
                if total_odd <= 2.30:
                    valid_combos.append({
                        "Combinatie": " + ".join([m['Match'] for m in combo]),
                        "Details": " x ".join([str(m['Odd']) for m in combo]),
                        "Totaal": round(total_odd, 2)
                    })
        
        if valid_combos:
            st.subheader("🎯 Voorgestelde Safe Slips")
            res_df = pd.DataFrame(valid_combos).sort_values(by="Totaal", ascending=False)
            st.dataframe(res_df, use_container_width=True, hide_index=True)
            
            # Opslaan in database
            sel = st.selectbox("Kies slip om op te slaan:", res_df['Combinatie'])
            if st.button("BEVESTIG & SLA OP IN CSV"):
                row = res_df[res_df['Combinatie'] == sel].iloc[0]
                new_entry = {
                    "Tijd": datetime.now().strftime("%H:%M"),
                    "Combinatie": row['Combinatie'],
                    "Totale_Odd": row['Totaal']
                }
                st.session_state.archief = pd.concat([st.session_state.archief, pd.DataFrame([new_entry])], ignore_index=True)
                st.toast("Opgeslagen in database!")
        else:
            st.warning("Geen combinaties gevonden onder de 2.30.")
    else:
        st.error("Kon geen wedstrijden vinden met odds tussen 1.15 en 1.40 in deze tekst.")

# --- ARCHIEF ---
st.divider()
st.subheader("📊 Mijn Database (Over 1.5 Slips)")
st.dataframe(st.session_state.archief, use_container_width=True)

if not st.session_state.archief.empty:
    csv = st.session_state.archief.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Database", csv, "over15_db.csv", "text/csv")
