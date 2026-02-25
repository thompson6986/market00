import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Thai 0-0 Scanner", page_icon="🇹🇭")

st.title("🇹🇭 Thai League: 0-0 Analyser")
st.write("Kopieer de 'Correct Score' tabel van OddsPortal en plak deze hieronder.")

# Het tekstveld voor de geplakte data
input_data = st.text_area("Plak hier je OddsPortal data:", height=300, placeholder="Bijv: 0:0 9.50 bet365...")

def extract_odds(text):
    # We zoeken naar patronen zoals "0:0" gevolgd door een getal (de odd)
    results = []
    
    # Splits de tekst in regels
    lines = text.split('\n')
    
    for i, line in enumerate(lines):
        # We zoeken specifiek naar de tekst "0:0"
        if "0:0" in line:
            # We kijken in de buurt van "0:0" naar getallen die op odds lijken (bijv. 8.50 of 11.00)
            # We zoeken naar het eerste getal met 2 decimalen na de '0:0'
            following_text = " ".join(lines[i:i+3]) # Pak ook de volgende regels mee
            odd_match = re.search(r'(\d{1,2}\.\d{2})', following_text)
            
            if odd_match:
                results.append({
                    "Uitslag": "0-0",
                    "Gevonden Odd": odd_match.group(1),
                    "Context": line[:50] # Laat een stukje van de regel zien ter controle
                })
    
    return pd.DataFrame(results)

if st.button('SCAN MIJN DATA'):
    if input_data:
        df = extract_odds(input_data)
        if not df.empty:
            st.success("0-0 Odds succesvol gevonden!")
            st.dataframe(df, use_container_width=True)
            
            # Professionele berekening
            min_odd = df['Gevonden Odd'].astype(float).min()
            max_odd = df['Gevonden Odd'].astype(float).max()
            st.metric("Hoogste 0-0 Odd", f"{max_odd}")
            st.info(f"Met een inzet van 1 unit win je bij de hoogste odd {max_odd} units.")
        else:
            st.warning("Geen '0:0' patroon gevonden. Heb je de juiste tabel gekopieerd?")
    else:
        st.error("Plak eerst data in het tekstvak.")

st.divider()
st.caption("Tip: Selecteer op OddsPortal de tabel vanaf 'Correct Score' tot het einde van de lijst.")
