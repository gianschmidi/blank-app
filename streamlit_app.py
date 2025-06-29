import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from fitparse import FitFile

# --- FIT-Datei einlesen ---
def read_fit_power_data(fit_path):
    fitfile = FitFile(fit_path)
    records = []
    for record in fitfile.get_messages('record'):
        fields = record.as_dict()['fields']
        time = None
        power = None
        for field in fields:
            if field['name'] == 'timestamp':
                time = field['value']
            elif field['name'] == 'power':
                power = field['value']
        if time is not None and power is not None:
            records.append({'timestamp': time, 'power': power})
    df = pd.DataFrame(records)
    df['seconds'] = (df['timestamp'] - df['timestamp'].iloc[0]).dt.total_seconds()
    return df

# --- Rolling Average für Bestwerte ---
def best_average_power(df, window_seconds):
    window_size = int(window_seconds)  # Annahme: 1 Hz Samplingrate
    if len(df) < window_size:
        return np.nan
    rolling = df['power'].rolling(window=window_size, min_periods=window_size).mean()
    return rolling.max()

# --- Power Profile berechnen ---
def compute_power_profile(df, intervals):
    profile = {}
    for sec in intervals:
        profile[sec] = best_average_power(df, sec)
    return profile

# --- Critical Power berechnen (lineare Regression) ---
def estimate_critical_power(profile):
    # Nur Zeit > 2min verwenden (z.B. 180s, 360s, 720s)
    times = np.array([t for t in profile.keys() if t >= 180])
    powers = np.array([profile[t] for t in times])
    X = 1 / times
    coeffs = np.polyfit(X, powers, 1)
    cp = coeffs[1]  # Achsenabschnitt entspricht Critical Power
    return cp

# --- Visualisierung ---
def plot_power_profile(profile, cp):
    times = np.array(list(profile.keys()))
    powers = np.array(list(profile.values()))
    plt.figure(figsize=(8, 5))
    plt.plot(times/60, powers, marker='o', label='Bestwerte')
    plt.axhline(cp, color='r', linestyle='--', label=f'Critical Power: {cp:.0f} W')
    plt.xlabel('Zeit (min)')
    plt.ylabel('Leistung (W)')
    plt.title('Power Profile & Critical Power')
    plt.legend()
    plt.grid(True)
    plt.show()

# --- Hauptprogramm ---
if __name__ == "__main__":
    fit_path = "deine_datei.fit"
    intervals = [20, 180, 360, 720]  # 20s, 3min, 6min, 12min
    df = read_fit_power_data(fit_path)
    profile = compute_power_profile(df, intervals)
    cp = estimate_critical_power(profile)
    plot_power_profile(profile, cp)
