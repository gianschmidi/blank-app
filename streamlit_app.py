# app.py

import streamlit as st
from fitparse import FitFile
import pandas as pd
import numpy as np
import plotly.express as px

# ---- PARAMETER ---- #
ZEITSPANNEN = {
    "20 Sekunden": 20,
    "3 Minuten": 180,
    "6 Minuten": 360,
    "12 Minuten": 720
}

# Beispielhafte Coggan-Werte (W/kg) für jede Kategorie
COGGAN_CATEGORIES = {
    "20 Sekunden": [5, 7, 9, 12],  # W/kg: Anfänger bis Elite
    "3 Minuten": [3, 4, 5, 7],
    "6 Minuten": [2.8, 4, 5, 6.5],
    "12 Minuten": [2.5, 3.5, 4.5, 6]
}

CATEGORY_LABELS = ["Untrainiert", "Fortgeschritten", "Gut", "Sehr gut", "Elite"]

# ---- FUNKTIONEN ---- #

def lade_fit_datei(uploaded_file):
    fitfile = FitFile(uploaded_file)
    daten = []
    for record in fitfile.get_messages('record'):
        values = record.get_values()
        if 'power' in values and 'timestamp' in values:
            daten.append([values['timestamp'], values['power']])
    df = pd.DataFrame(daten, columns=['timestamp', 'power'])
    return df

def berechne_bestwert(df, intervall):
    """Berechnet den höchsten gleitenden Durchschnitt für ein Intervall in Sekunden"""
    df = df.copy()
    df = df.sort_values('timestamp')
    df['power'] = df['power'].fillna(0)
    df['delta'] = df['timestamp'].diff().dt.total_seconds().fillna(1)
    abtastrate = df['delta'].median()
    fenster = max(int(intervall / abtastrate), 1)
    df['rolling_mean'] = df['power'].rolling(window=fenster).mean()
    return df['rolling_mean'].max()

def ermittle_fahrertyp(watt_pro_kg, kategorie_werte):
    """Findet passende Kategorie"""
    for idx, wert in enumerate(kategorie_werte):
        if watt_pro_kg < wert:
            return CATEGORY_LABELS[idx]
    return CATEGORY_LABELS[-1]

# ---- STREAMLIT APP ---- #

st.set_page_config(page_title="🚴 Power Profiling App", layout="centered")
st.title("🚴 Power Profiling & Leistungs-Bestwerte")
st.write("""
Lade deine `.fit`-Datei hoch, gib dein Gewicht ein und finde dein Power Profil heraus!
""")

gewicht = st.number_input("Dein Gewicht (in kg):", min_value=30.0, max_value=120.0, value=70.0, step=0.5)

uploaded_file = st.file_uploader("📂 FIT-Datei auswählen", type=["fit"])

if uploaded_file is not None:
    with st.spinner('📊 Datei wird verarbeitet...'):
        df = lade_fit_datei(uploaded_file)
        results = []
        for name, sekunden in ZEITSPANNEN.items():
            bestwert = berechne_bestwert(df, sekunden)
            watt_pro_kg = bestwert / gewicht
            kategorie = ermittle_fahrertyp(watt_pro_kg, COGGAN_CATEGORIES[name])
            results.append({
                "Intervall": name,
                "Bestwert (Watt)": round(bestwert, 1),
                "W/kg": round(watt_pro_kg, 2),
                "Kategorie": kategorie
            })

        result_df = pd.DataFrame(results)
        st.success("✅ Analyse abgeschlossen!")
        st.dataframe(result_df, use_container_width=True)

        # Power Curve
        fig = px.line(
            result_df,
            x="Intervall",
            y="W/kg",
            title="🔋 Power Profil (W/kg)",
            markers=True
        )
        st.plotly_chart(fig, use_container_width=True)

        # CSV Download
        csv = result_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Ergebnisse als CSV herunterladen",
            data=csv,
            file_name='power_profil.csv',
            mime='text/csv',
        )

        st.info("""
        ℹ️ **Hinweis:** Die Kategorien basieren auf vereinfachten Coggan-Werten und dienen nur als grobe Einordnung.
        """)
else:
    st.info("⬆️ Bitte lade eine `.fit`-Datei hoch, um deine Bestwerte zu berechnen.")
