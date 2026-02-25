import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Thai 0-0 Pro Scanner", page_icon="🇹🇭")

st.title("🇹🇭 Thai League: 0-0 Analyser")
st.markdown("Kopieer de tekst van OddsPortal en plak deze hieronder.")

input_data = st.text_area("Plak hier de data:", height=250)

def super_scan(text):
    results = []
    # We splitsen op regels en verwijderen lege regels
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    
    # We zoeken naar patronen: '0:0', '0-0', of regels met 'CS' (Correct Score)
    for i, line in enumerate(lines):
        # Zoek naar de 0-0 aanduiding
        if "0:0" in line or "0-0" in line:
            # Pak de omgeving van de 0-0 (deze regel en de volgende 3)
            search_area = " ".join(lines[i:i+4])
            
            # Zoek naar alle getallen met een punt (bijv 9.50, 11.00)
            odds = re.findall(r'\b\d{1,2}\.\d{2}\b', search_area)
            
            if odds:
                # In de tabel van OddsPortal is de eerste odd vaak de hoogste of de gemiddelde
                # We pakken de hoogste waarde uit de gevonden getallen
                float_odds = [float(o) for o in odds]
                best_odd = max(float_odds)
                
                # Probeer de wedstrijd te vinden (vaak een paar regels erboven)
                match_name = "Wedstrijd gevonden via 0-0 scan"
                for j in range(i, max(-1, i-10), -1):
                    if " - " in lines[j] and ":" not in lines[j]:
                        match_name = lines[j]
                        break
                
                results.append({
                    "Wedstrijd": match_name,
                    "Uitslag": "0-0",
                    "Hoogste Odd": best_odd
                })

    return pd.DataFrame(results).drop_duplicates(subset=['Wedstrijd'])

if st.button('ANALYSEER DATA'):
    if input_data:
        df = super_scan(input_data)
        if not df.empty:
            st.success(f"Gevonden: {len(df)} 0-0 odds!")
            st.table(df)
            
            # Professionele berekening op basis van 1 unit inzet
            for _, row in df.iterrows():
                winst = row['Hoogste Odd'] - 1
                st.write(f"👉 **{row['Wedstrijd']}**: Inzet 1 unit -> Winst: **{winst:.2f}** units.")
        else:
            st.error("Nog steeds geen odds gevonden.")
            st.info("💡 **Gouden Tip voor OddsPortal:** Klik op de wedstrijd -> 'Correct Score'. Selecteer dan met je muis de tekst vanaf '0:0' tot en met de getallen die erachter staan. Plak dat hier.")
    else:
        st.write("Plak eerst data.")
