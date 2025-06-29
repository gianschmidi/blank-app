import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from fitparse import FitFile

# Hilfsfunktion: FIT-Datei einlesen
def read_fit_power_data(uploaded_file):
    fitfile = FitFile(uploaded_file)
    records = []
    for record in fitfile.get_messages('record'):
        record_dict = record.get_values()
        if 'timestamp' in record_dict and 'power' in record_dict:
            records.append({
                'timestamp': pd.to_datetime(record_dict['timestamp']),
                'power': record_dict['power']
            })
    if not records:
        return pd.DataFrame()
    df = pd.DataFrame(records)
    df['seconds'] = (df['timestamp'] - df['timestamp'].iloc[0]).dt.total_seconds()
    return df

# Hilfsfunktion: Maximale Durchschnittsleistung für ein Zeitfenster
def best_average_power(df, window_seconds):
    window_size = int(window_seconds)
    if len(df) < window_size:
        return np.nan
    return df['power'].rolling(window=window_size, min_periods=window_size).mean().max()

# Power Profile berechnen
def compute_power_profile(df, intervals):
    return {sec: best_average_power(df, sec) for sec in intervals}

# Critical Power schätzen (lineare Regression)
def estimate_critical_power(profile):
    # Nur Zeitpunkte >= 3min (180s) verwenden
    times = np.array([t for t in profile.keys() if t >= 180])
    powers = np.array([profile[t] for t in times])
    if len(times) < 2:
        return np.nan
    X = 1 / times
    coeffs = np.polyfit(X, powers, 1)
    return coeffs[1]  # y-Achsenabschnitt = Critical Power

# Streamlit App
st.set_page_config(page_title="Power Profile & Critical Power Analyse", layout="centered")
st.title('🚴 Power Profile & Critical Power Analyse')
st.write("Lade eine FIT-Datei mit Leistungsdaten hoch, um dein Power Profile und deine Critical Power zu berechnen.")

uploaded_file = st.file_uploader('FIT-Datei hochladen', type=['fit'])

if uploaded_file:
    df = read_fit_power_data(uploaded_file)
    if df.empty:
        st.error('Keine Leistungsdaten gefunden. Bitte wähle eine andere Datei.')
    else:
        intervals = [20, 180, 360, 720]  # 20s, 3min, 6min, 12min
        profile = compute_power_profile(df, intervals)
        cp = estimate_critical_power(profile)

        st.subheader('Ergebnisse')
        st.write(pd.DataFrame({
            "Intervall (s)": intervals,
            "Leistungs-Bestwert (W)": [profile[t] for t in intervals]
        }))

        if not np.isnan(cp):
            st.success(f"**Critical Power:** {cp:.0f} W")
        else:
            st.warning("Critical Power konnte nicht berechnet werden (zu wenig Daten für lange Intervalle).")

        # Diagramm
        fig, ax = plt.subplots(figsize=(8, 5))
        times = np.array(intervals) / 60  # Minuten
        powers = np.array([profile[t] for t in intervals])
        ax.plot(times, powers, 'bo-', label='Power Profile')
        if not np.isnan(cp):
            ax.axhline(cp, color='r', linestyle='--', label=f'Critical Power: {cp:.0f} W')
        ax.set_xlabel('Zeitintervall (min)')
        ax.set_ylabel('Leistung (W)')
        ax.set_title('Power Profile')
        ax.grid(True, which='both', ls='--')
        ax.legend()
        st.pyplot(fig)

else:
    st.info("Bitte lade eine FIT-Datei hoch.")

st.markdown("---")
st.caption("Erstellt mit ❤️ und [fitparse](https://github.com/dtcooper/python-fitparse).")
