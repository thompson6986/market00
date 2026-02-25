import streamlit as st
import pandas as pd
import re
from datetime import datetime
import io

st.set_page_config(page_title="Pro Betting Database", page_icon="📊", layout="wide")

# Initialiseer het archief
if 'archief' not in st.session_state:
    st.session_state.archief = pd.DataFrame(columns=["Tijdstip", "Wedstrijd", "Odd", "Inzet", "Pot. Winst"])

st.title("⚽ Professional 0-0 Database & Tracker")

# --- ZIJB BALK: DATA BEHEER ---
with st.sidebar:
    st.header("📂 Data Beheer")
    uploaded_file = st.file_uploader("Upload een eerder archief (CSV)", type="csv")
    
    if uploaded_file is not None:
        if st.button("Importeer CSV Data"):
            try:
                uploaded_df = pd.read_csv(uploaded_file)
                # Voeg geüploade data toe aan huidige sessie en verwijder dubbelen
                st.session_state.archief = pd.concat([st.session_state.archief, uploaded_df], ignore_index=True).drop_duplicates()
                st.success("Data succesvol geïmporteerd!")
            except Exception as e:
                st.error(f"Fout bij laden: {e}")

    if st.button("🗑️ Wis Volledig Archief"):
        st.session_state.archief = pd.DataFrame(columns=["Tijdstip", "Wedstrijd", "Odd", "Inzet", "Pot. Winst"])
        st.rerun()

# --- HOOFDSCHERM: SCANNER ---
st.subheader("🔍 Nieuwe Odds Scannen")
input_data = st.text_area("Plak hier de data van OddsPortal:", height=150)

def super_scan(text):
    results = []
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    for i, line in enumerate(lines):
        if "0:0" in line or "0-0" in line:
            search_area = " ".join(lines[i:i+4])
            odds = re.findall(r'\b\d{1,2}\.\d{2}\b', search_area)
            if odds:
                float_odds = [float(o) for o in odds]
                best_odd = max(float_odds)
                match_name = "Onbekende wedstrijd"
                for j in range(i, max(-1, i-10), -1):
                    if " - " in lines[j] and ":" not in lines[j]:
                        match_name = lines[j]
                        break
                results.append({"Wedstrijd": match_name, "Odd": best_odd})
    return pd.DataFrame(results).drop_duplicates(subset=['Wedstrijd'])

col_scan, col_add = st.columns([2, 1])

with col_scan:
    if st.button('ANALYSEER DATA'):
        if input_data:
            df_scan = super_scan(input_data)
            if not df_scan.empty:
                st.session_state.last_scan = df_scan
                st.table(df_scan)
            else:
                st.error("Geen data gevonden.")

with col_add:
    if 'last_scan' in st.session_state:
        st.markdown("### 💾 Opslaan")
        selected_match = st.selectbox("Selecteer match:", st.session_state.last_scan['Wedstrijd'])
        inzet = st.number_input("Inzet (units):", min_value=1.0, value=1.0, step=1.0)
        
        if st.button("VOEG TOE AAN LIJST"):
            match_info = st.session_state.last_scan[st.session_state.last_scan['Wedstrijd'] == selected_match].iloc[0]
            nieuwe_rij = {
                "Tijdstip": datetime.now().strftime("%d-%m %H:%M"),
                "Wedstrijd": selected_match,
                "Odd": match_info['Odd'],
                "Inzet": inzet,
                "Pot. Winst": round(match_info['Odd'] * inzet, 2)
            }
            st.session_state.archief = pd.concat([st.session_state.archief, pd.DataFrame([nieuwe_rij])], ignore_index=True)
            st.toast(f"Opgeslagen: {selected_match}")

# --- HET ARCHIEF ---
st.divider()
st.subheader("📊 Jouw Betting Archief")

if not st.session_state.archief.empty:
    # We tonen de tabel
    st.dataframe(st.session_state.archief, use_container_width=True, hide_index=True)
    
    # Statistieken balk
    c1, c2, c3 = st.columns(3)
    totaal_inzet = st.session_state.archief['Inzet'].sum()
    totaal_pot_winst = st.session_state.archief['Pot. Winst'].sum()
    
    c1.metric("Totaal Ingezet", f"{totaal_inzet} units")
    c2.metric("Potentiële Omzet", f"{totaal_pot_winst:.2f} units")
    c3.metric("Aantal Bets", len(st.session_state.archief))

    # Download knop
    csv = st.session_state.archief.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Archief als CSV",
        data=csv,
        file_name=f"betting_archive_{datetime.now().strftime('%Y-%m-%d')}.csv",
        mime="text/csv",
    )
else:
    st.info("Het archief is momenteel leeg. Scan data of upload een oud CSV bestand.")
