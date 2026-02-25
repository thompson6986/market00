import streamlit as st
import pandas as pd
import re

# Deze regel MOET altijd als eerste staan na de imports
st.set_page_config(page_title="Thai 0-0 Pro Scanner", page_icon="🇹🇭")

st.title("🇹🇭 Thai League: 0-0 Analyser")
st.markdown("""
**Hoe gebruik je dit?**
1. Ga naar **OddsPortal** (Thai League 1 - Correct Score).
2. Kopieer de hele tabel (`Ctrl+A` -> `Ctrl+C`).
3. Plak het hieronder en klik op de knop.
""")

# Input veld voor de geplakte data
input_data = st.text_area("Plak hier je OddsPortal data:", height=250, placeholder="Plak de tekst hier...")

def extract_odds_simple(text):
    results = []
    # We splitsen de tekst in blokken per mogelijke wedstrijd/bookmaker
    lines = text.split('\n')
    
    current_match = "Onbekende wedstrijd"
    
    for i, line in enumerate(lines):
        # Stap 1: Zoek naar team namen (bevatten vaak ' - ')
        if " - " in line and ":" not in line:
            current_match = line.strip()
            
        # Stap 2: Zoek naar de 0:0 score
        if "0:0" in line:
            # We zoeken naar het getal (de odd) in de buurt van '0:0'
            # We scannen de huidige en de volgende 2 regels
            context = " ".join(lines[i:i+3])
            # Zoek naar een getal zoals 8.50, 10.0, 12.5 etc.
            odd_matches = re.findall(r'\d{1,2}\.\d{2}', context)
            
            if odd_matches:
                # We pakken de hoogste odd die we in dit blokje vinden
                best_odd = max([float(o) for o in odd_matches])
                results.append({
                    "Wedstrijd": current_match,
                    "Uitslag": "0-0",
                    "Beste Odd": best_odd
                })
    
    return pd.DataFrame(results).drop_duplicates(subset=['Wedstrijd'])

if st.button('BEREKEN HOOGSTE ODDS'):
    if input_data:
        with st.spinner('Data analyseren...'):
            df = extract_odds_simple(input_data)
            if not df.empty:
                st.success(f"Gevonden: {len(df)} wedstrijden")
                # Sorteer op de hoogste odd
                df = df.sort_values(by="Beste Odd", ascending=False)
                st.table(df)
                
                # Berekening voor de gebruiker
                top_match = df.iloc[0]
                st.info(f"💡 **Tip:** De beste kans is momenteel **{top_match['Wedstrijd']}** met een odd van **{top_match['Beste Odd']}**.")
            else:
                st.warning("Geen '0:0' scores gevonden in de geplakte tekst. Probeer de hele pagina te kopiëren.")
    else:
        st.error("Plak eerst de data van OddsPortal.")

st.divider()
st.caption("Gebruikt geen externe API's - 100% stabiel voor de Thaise markt.")
