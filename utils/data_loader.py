"""
Data loader for AP-WRIMS Early Warning System.
Loads MI Tank, Reservoir, Soil Moisture and Rainfall CSVs for
Kadapa/YSR and Annamayya districts.
"""

import os
import pandas as pd
import numpy as np

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Data")

# File name mappings
MITANK_FILES = {
    "Nov17": "MITANK_FILL_REPORT_11-17-2021.csv",
    "Nov18": "MITANK_FILL_REPORT_18-11-2021.csv",
    "Nov19": "MITANK_FILL_REPORT_19-11-2021.csv",
    "Nov20": "MITANK_FILL_REPORT_20-11-2021.csv",
    "Current": "MITANK_FILL_REPORT_1776370982795.csv",
}

RESERVOIR_FILES = {
    "Nov17": "Reservoir Summary_17-11-2021.csv",
    "Nov18": "Reservoir Summary_18-11-2021.csv",
    "Nov19": "Reservoir Summary_19-11-2021.csv",
    "Nov20": "Reservoir Summary_20-11-2021.csv",
    "Current": "Reservoir Summary_1776370273977.csv",
}

SOIL_FILES = {
    "Nov17": "Soil moisture summary_17-11-2021.csv",
    "Nov18": "Soil moisture summary_18-11-2021.csv",
    "Nov19": "Soil moisture summary_19-11-2021.csv",
    "Nov20": "Soil moisture summary_20-11-2021.csv",
    "Current": "Soil moisture summary_1776371098636.csv",
}

RAINFALL_FILES = {
    "Nov2021": "Rainfall_Summary_01-11-2021_30-11-2021.csv",
    "Current": "Rainfall_Summary_1776370356937.csv",
}

# District name variants as they appear in the raw CSVs
YSR_VARIANTS = {"y.s.r kadapa", "y.s.r. kadapa", "y.s.r.kadapa", "ysr kadapa"}
ANNAMAYYA_VARIANTS = {"annamayya"}


def _norm(val):
    """Normalise a string for district matching."""
    return str(val).strip().lower()


def _to_float(val, default=0.0):
    """Safely convert a value to float, returning default for missing/dash."""
    try:
        s = str(val).strip()
        if s in ("-", "", "nan", "None"):
            return default
        return float(s)
    except (ValueError, TypeError):
        return default


# ---------------------------------------------------------------------------
# MI Tank loader
# ---------------------------------------------------------------------------

def _load_mitank(date_key: str) -> dict:
    """Return mi_tank_fill_pct for YSR Kadapa on a given date key."""
    path = os.path.join(DATA_DIR, MITANK_FILES[date_key])
    df = pd.read_csv(path, skiprows=2, header=0, dtype=str)
    # Row 0 is the sub-header row (Total / Fill % etc) — skip it
    df = df.iloc[1:].reset_index(drop=True)
    # Fill % is in the 5th column (index 4, labelled 'Unnamed: 4' or 'Fill (%)')
    fill_col = df.columns[4]
    district_col = df.columns[0]

    ysr_row = df[df[district_col].apply(_norm).isin(YSR_VARIANTS)]
    fill_pct = _to_float(ysr_row[fill_col].values[0]) if not ysr_row.empty else 0.0
    return {"mi_tank_fill_pct": fill_pct}


# ---------------------------------------------------------------------------
# Reservoir loader
# ---------------------------------------------------------------------------

def _load_reservoir(date_key: str) -> dict:
    """Return Pincha and Annamayya (Cheyyeru) inflow/outflow for a date key."""
    path = os.path.join(DATA_DIR, RESERVOIR_FILES[date_key])
    df = pd.read_csv(path, skiprows=2, header=0, dtype=str)
    # Row 0 is the sub-header row — skip it
    df = df.iloc[1:].reset_index(drop=True)
    # Column positions: 0=Reservoir, 7=Inflow, 8=Outflow
    res_col = df.columns[0]
    inflow_col = df.columns[7]
    outflow_col = df.columns[8]

    df[res_col] = df[res_col].str.strip().str.upper()

    pincha = df[df[res_col].str.contains("PINCHA", na=False)]
    cheyyeru = df[df[res_col].str.contains("CHEYYERU|ANNAMAYYA.*RESERVOIR", na=False, regex=True)]

    pincha_inflow = _to_float(pincha[inflow_col].values[0]) if not pincha.empty else 0.0
    pincha_outflow = _to_float(pincha[outflow_col].values[0]) if not pincha.empty else 0.0

    if cheyyeru.empty:
        ann_inflow, ann_outflow, sensor_dead = 0.0, 0.0, True
    else:
        raw_in = str(cheyyeru[inflow_col].values[0]).strip()
        raw_out = str(cheyyeru[outflow_col].values[0]).strip()
        sensor_dead = raw_in in ("-", "", "nan", "None")
        ann_inflow = _to_float(raw_in)
        ann_outflow = _to_float(raw_out)

    return {
        "pincha_inflow": pincha_inflow,
        "pincha_outflow": pincha_outflow,
        "annamayya_inflow": ann_inflow,
        "annamayya_outflow": ann_outflow,
        "annamayya_sensor_dead": sensor_dead,
    }


# ---------------------------------------------------------------------------
# Soil moisture loader
# ---------------------------------------------------------------------------

def _load_soil(date_key: str) -> dict:
    """Return soil moisture % at 100 cm for YSR Kadapa on a given date key."""
    path = os.path.join(DATA_DIR, SOIL_FILES[date_key])
    df = pd.read_csv(path, skiprows=2, header=0, dtype=str)
    # Soil files have no sub-header row after skiprows=2 — data starts immediately.
    # If the first row looks like a sub-header (DISTRICT col is NaN), drop it.
    if _norm(df.iloc[0, 0]) in ("nan", ""):
        df = df.iloc[1:].reset_index(drop=True)

    district_col = df.columns[0]
    # 100 cm % is the 7th column (index 6)
    moisture_col = df.columns[6]

    ann_row = df[df[district_col].apply(_norm).isin(ANNAMAYYA_VARIANTS)]
    moisture = _to_float(ann_row[moisture_col].values[0]) if not ann_row.empty else 0.0
    return {"soil_moisture_100cm": moisture}


# ---------------------------------------------------------------------------
# Rainfall loader
# ---------------------------------------------------------------------------

def _load_rainfall_nov2021() -> dict:
    """Return Nov 2021 monthly rainfall stats for YSR Kadapa."""
    path = os.path.join(DATA_DIR, RAINFALL_FILES["Nov2021"])
    df = pd.read_csv(path, skiprows=2, header=0, dtype=str)
    # Row 0 is sub-header (Normal mm / Actual mm etc) — skip it
    df = df.iloc[1:].reset_index(drop=True)
    district_col = df.columns[0]
    normal_col = df.columns[1]
    actual_col = df.columns[2]
    deviation_col = df.columns[3]

    ysr_row = df[df[district_col].apply(_norm).isin(YSR_VARIANTS)]
    if ysr_row.empty:
        return {"rainfall_actual": 0.0, "rainfall_normal": 0.0, "rainfall_anomaly_pct": 0.0}

    normal = _to_float(ysr_row[normal_col].values[0])
    actual = _to_float(ysr_row[actual_col].values[0])
    deviation = _to_float(ysr_row[deviation_col].values[0])
    return {
        "rainfall_actual": actual,
        "rainfall_normal": normal,
        "rainfall_anomaly_pct": deviation,
    }


def _load_rainfall_current() -> dict:
    """Return current rainfall stats for YSR Kadapa from the 2026 summary file."""
    path = os.path.join(DATA_DIR, RAINFALL_FILES["Current"])
    df = pd.read_csv(path, skiprows=2, header=0, dtype=str)
    # Row 0 is sub-header — skip it
    df = df.iloc[1:].reset_index(drop=True)
    district_col = df.columns[0]

    # The 2026 file has columns for multiple periods; use the last cumulative period:
    # Jun 01-2025 - Apr 17-2026 → columns at positions 7 (Normal), 8 (Actual), 9 (Deviation)
    normal_col = df.columns[7]
    actual_col = df.columns[8]
    deviation_col = df.columns[9]

    ysr_row = df[df[district_col].apply(_norm).isin(YSR_VARIANTS)]
    if ysr_row.empty:
        return {"rainfall_actual": 0.0, "rainfall_normal": 0.0, "rainfall_anomaly_pct": 0.0}

    normal = _to_float(ysr_row[normal_col].values[0])
    actual = _to_float(ysr_row[actual_col].values[0])
    deviation = _to_float(ysr_row[deviation_col].values[0])
    return {
        "rainfall_actual": actual,
        "rainfall_normal": normal,
        "rainfall_anomaly_pct": deviation,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_date_data(date_key: str) -> dict:
    """
    Load and merge all data sources for a given date key.

    Parameters
    ----------
    date_key : str
        One of 'Nov17', 'Nov18', 'Nov19', 'Nov20', 'Current'.

    Returns
    -------
    dict with keys:
        mi_tank_fill_pct, soil_moisture_100cm,
        pincha_inflow, pincha_outflow,
        annamayya_inflow, annamayya_outflow, annamayya_sensor_dead,
        rainfall_actual, rainfall_normal, rainfall_anomaly_pct
    """
    result = {}
    result.update(_load_mitank(date_key))
    result.update(_load_reservoir(date_key))
    result.update(_load_soil(date_key))

    if date_key == "Current":
        result.update(_load_rainfall_current())
    else:
        result.update(_load_rainfall_nov2021())

    # Ensure correct types
    for k in ("mi_tank_fill_pct", "soil_moisture_100cm",
              "pincha_inflow", "pincha_outflow",
              "annamayya_inflow", "annamayya_outflow",
              "rainfall_actual", "rainfall_normal", "rainfall_anomaly_pct"):
        result[k] = float(result.get(k, 0.0))
    result["annamayya_sensor_dead"] = bool(result.get("annamayya_sensor_dead", False))

    return result


def load_all_dates() -> dict:
    """Return a dict keyed by date_key containing loaded data for every date."""
    dates = ["Nov17", "Nov18", "Nov19", "Nov20", "Current"]
    return {d: load_date_data(d) for d in dates}
