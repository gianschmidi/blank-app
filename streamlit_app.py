def read_fit_power_data(uploaded_file):
    """Liest Leistungsdaten aus FIT-Datei"""
    fitfile = FitFile(uploaded_file)
    records = []
    for record in fitfile.get_messages('record'):
        time, power = None, None
        for field in record.as_dict()['fields']:
            if field['name'] == 'timestamp': time = field['value']
            elif field['name'] == 'power': power = field['value']
        if time and power: records.append({'timestamp': time, 'power': power})
    
    if not records: return pd.DataFrame()
    df = pd.DataFrame(records)
    df['seconds'] = (df['timestamp'] - df['timestamp'].iloc[0]).dt.total_seconds()
    return df

def best_average_power(df, window_seconds):
    """Berechnet maximale Durchschnittsleistung für Zeitfenster"""
    window_size = int(window_seconds)
    if len(df) < window_size: return np.nan
    return df['power'].rolling(window=window_size, min_periods=window_size).mean().max()

def compute_power_profile(df, intervals):
    """Erstellt Power-Profile für definierte Intervalle"""
    return {sec: best_average_power(df, sec) for sec in intervals}

def estimate_critical_power(profile):
    """Berechnet Critical Power mittels linearer Regression"""
    times = np.array([t for t in profile.keys() if t >= 180])
    powers = np.array([profile[t] for t in times])
    if len(times) < 2: return np.nan  # Mind. 2 Punkte benötigt
    X = 1 / times
    coeffs = np.polyfit(X, powers, 1)
    return coeffs[1]  # y-Achsenabschnitt = Critical Power

# Streamlit UI

uploaded_file = st.file_uploader('FIT-Datei hochladen', type=['fit'],

if uploaded_file:
    df = read_fit_power_data(uploaded_file)
    if df.empty:
        st.error('Keine Leistungsdaten gefunden. Bitte andere Datei wählen.')
    else:
        intervals = [20, 180, 360, 720]  # 20s, 3min, 6min, 12min
        profile = compute_power_profile(df, intervals)
        cp = estimate_critical_power(profile)
        
        # Ergebnisanzeige
        st.subheader('Ergebnisse')
        col1, col2 = st.columns(2)
        col1.metric("Critical Power", f"{cp:.0f} W" if not np.isnan(cp) else "N/A")
        
        with col2:
            st.write("**Power Profile:**")
            for sec, power in profile.items():
                st.write(f"- {sec}s: {power:.0f} W")
        
        # Diagramm
        fig, ax = plt.subplots(figsize=(10, 6))
        times = list(profile.keys())
        powers = list(profile.values())
        
        ax.plot(np.array(times)/60, powers, 'bo-', label='Leistungs-Bestwerte')
        if not np.isnan(cp):
            ax.axhline(cp, color='r', linestyle='--', label=f'Critical Power: {cp:.0f} W')
        
        ax.set_xscale('log')
        ax.set_xticks([20/60, 3, 6, 12])
        ax.set_xticklabels(['20s', '3m', '6m', '12m'])
        ax.set_xlabel('Zeitintervall')
        ax.set_ylabel('Leistung (W)')
        ax.set_title('Power Profile')
        ax.grid(True, which='both', ls='--')
        ax.legend()
        
        st.pyplot(fig)

# Installationshinweis im Sidebar
with st.sidebar:
    st.info("**Voraussetzungen:**\n``````")
