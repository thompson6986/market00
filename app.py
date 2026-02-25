# --- SELECTIE EN OPSLAAN (Met handmatige naamgeving) ---
if 'current_scan' in st.session_state:
    st.divider()
    st.subheader("🎯 Voeg toe aan je Dagelijkse Slips")
    df = st.session_state.current_scan
    
    # We tonen de ruwe data zodat je ziet wat je geplakt hebt
    st.dataframe(df, use_container_width=True, hide_index=True)

    c1, c2, c3 = st.columns([2, 1, 1])
    
    with c1:
        # Stap 1: Selecteer de gescande rij
        sel_row_idx = st.selectbox("Selecteer de gescande regel:", df.index, format_func=lambda x: f"Gevonden odd: {df.loc[x, '0-0']}")
        
        # Stap 2: GEEF HIER DE WEDSTRIJD EEN NAAM
        gekozen_naam = st.text_input("Geef de wedstrijd een naam:", value=df.loc[sel_row_idx, 'Match'])

    with c2:
        row = df.loc[sel_row_idx]
        # Zoek alle beschikbare odds in de rij
        opties = {k: v for k, v in row.items() if k in ["1", "X", "2", "0-0"] and v != "N/A"}
        keuze = st.selectbox("Kies je Bet:", list(opties.keys()))
        odd_val = opties[keuze]
        
    with c3:
        doel = st.selectbox("Voor Slip:", [1.5, 2.0, 3.0, 5.0])
        if st.button("VOEG TOE AAN SLIP"):
            new_bet = {
                "Tijd": datetime.now().strftime("%H:%M"), # Je kunt dit ook handmatig aanpassen indien nodig
                "Slip Doel": f"Slip {doel}",
                "Competitie": row['Comp'] if 'Comp' in row else "Handmatig",
                "Wedstrijd": gekozen_naam, # Hier wordt je eigen naam gebruikt!
                "Keuze": keuze,
                "Odd": odd_val,
                "Inzet": 1.0
            }
            st.session_state.archief = pd.concat([st.session_state.archief, pd.DataFrame([new_bet])], ignore_index=True)
            st.toast(f"Opgeslagen als: {gekozen_naam}")
