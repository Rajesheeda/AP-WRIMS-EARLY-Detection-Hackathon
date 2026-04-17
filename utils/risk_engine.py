"""
Hybrid Risk Scoring Engine for AP-WRIMS Early Warning System.

Score = (soil_moisture_100cm/100 * 25)
      + (inflow_surge_rate * 25)
      + (discharge_imbalance * 20)
      + (rainfall_anomaly * 20)
      + (sensor_penalty * 10)
"""

from __future__ import annotations
import math


# Score thresholds
THRESHOLDS = {
    "LOW": (0, 30),
    "MEDIUM": (30, 55),
    "HIGH": (55, 75),
    "CRITICAL": (75, 101),
}


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def compute_risk(current: dict, previous: dict | None = None) -> dict:
    """
    Compute a hybrid risk score for a single date.

    Parameters
    ----------
    current  : dict — data for the date being scored (from data_loader)
    previous : dict | None — data for the prior date (used for surge rate).
               If None, surge rate is 0.

    Returns
    -------
    dict with keys:
        score           float 0-100
        level           str  LOW | MEDIUM | HIGH | CRITICAL
        confidence      float 0-100
        time_to_failure str
        top_factors     list of (factor_name, points) tuples, sorted descending
    """
    # --- Component 1: Soil moisture (0-25 pts) ----------------------------
    soil_pct = _clamp(current["soil_moisture_100cm"] / 100.0)
    soil_pts = soil_pct * 25.0

    # --- Component 2: Inflow surge rate (0-25 pts) -------------------------
    # Use Pincha inflow as the primary indicator; fall back to Annamayya.
    cur_inflow = current["pincha_inflow"] or current["annamayya_inflow"]
    if previous is not None:
        prev_inflow = previous["pincha_inflow"] or previous["annamayya_inflow"]
    else:
        prev_inflow = None

    if prev_inflow and prev_inflow > 0:
        surge = (cur_inflow - prev_inflow) / prev_inflow
        surge = max(surge, 0.0)          # ignore receding flows
    else:
        surge = 0.0
    # Scale: 1 point per 1% surge, capped at 25 pts (25% surge = max score)
    surge_pts = min(surge * 100.0, 25.0)

    # --- Component 3: Discharge imbalance (0-20 pts) -----------------------
    # Use Pincha reservoir (most critical chokepoint).
    # When outflow > inflow the dam is releasing more than it receives —
    # maximum downstream stress → score = 1.0.
    p_inflow = current["pincha_inflow"]
    p_outflow = current["pincha_outflow"]
    denom = max(p_inflow, p_outflow)
    if denom > 0:
        imbalance = abs(p_outflow - p_inflow) / denom
        if p_outflow > p_inflow:
            imbalance = 1.0           # reverse pressure = maximum stress
    else:
        imbalance = 0.0
    imbalance_pts = imbalance * 20.0

    # --- Component 4: Rainfall anomaly (0-20 pts) --------------------------
    normal = current["rainfall_normal"]
    actual = current["rainfall_actual"]
    if normal and normal > 0:
        rain_ratio = _clamp(min(actual / normal, 5.0) / 5.0)
    else:
        rain_ratio = 0.0
    rain_pts = rain_ratio * 20.0

    # --- Component 5: Sensor penalty (0-10 pts) ----------------------------
    # Dead = 10 pts; suspicious (identical reading to prior day) = 5 pts.
    sensor_dead = current["annamayya_sensor_dead"]
    if sensor_dead:
        sensor_pts = 10.0
    elif (
        previous is not None
        and current["annamayya_inflow"] > 0
        and current["annamayya_inflow"] == previous["annamayya_inflow"]
    ):
        sensor_pts = 5.0   # frozen/suspicious reading
    else:
        sensor_pts = 0.0

    # --- Total score -------------------------------------------------------
    score = soil_pts + surge_pts + imbalance_pts + rain_pts + sensor_pts
    score = _clamp(score, 0.0, 100.0)

    # --- Risk level --------------------------------------------------------
    level = "LOW"
    for lvl, (lo, hi) in THRESHOLDS.items():
        if lo <= score < hi:
            level = lvl
            break

    # --- Confidence --------------------------------------------------------
    # Penalise confidence when sensor is dead or previous data is unavailable.
    confidence = 95.0
    if sensor_dead:
        confidence -= 20.0
    if previous is None:
        confidence -= 15.0
    # Also reduce if inflow data is all zeros (sensor dropout)
    if cur_inflow == 0 and p_inflow == 0 if previous else cur_inflow == 0:
        confidence -= 10.0
    confidence = _clamp(confidence, 0.0, 100.0) * 100.0 / 100.0  # keep 0-100
    confidence = round(max(0.0, min(100.0, confidence)), 1)

    # --- Time to failure estimate -----------------------------------------
    time_to_failure = _estimate_tte(score, level, surge)

    # --- Top factors (sorted by contribution) ------------------------------
    factors = [
        ("Soil Moisture (100cm)", round(soil_pts, 1)),
        ("Inflow Surge Rate", round(surge_pts, 1)),
        ("Discharge Imbalance", round(imbalance_pts, 1)),
        ("Rainfall Anomaly", round(rain_pts, 1)),
        ("Sensor Dead Penalty", round(sensor_pts, 1)),
    ]
    top_factors = sorted(factors, key=lambda x: x[1], reverse=True)

    return {
        "score": round(score, 2),
        "level": level,
        "confidence": confidence,
        "time_to_failure": time_to_failure,
        "top_factors": top_factors,
        # Raw components (useful for display)
        "_components": {
            "soil_pts": round(soil_pts, 2),
            "surge_pts": round(surge_pts, 2),
            "imbalance_pts": round(imbalance_pts, 2),
            "rain_pts": round(rain_pts, 2),
            "sensor_pts": round(sensor_pts, 2),
        },
    }


def _estimate_tte(score: float, level: str, surge: float) -> str:
    """Provide a human-readable time-to-failure estimate based on score and surge."""
    if level == "CRITICAL":
        if surge > 0.5:
            return "< 6 hours"
        return "6 – 12 hours"
    elif level == "HIGH":
        if surge > 0.3:
            return "12 – 24 hours"
        return "24 – 48 hours"
    elif level == "MEDIUM":
        return "2 – 5 days"
    else:
        return "> 7 days"


def compute_all_risks(all_data: dict) -> dict:
    """
    Compute risk scores for every date in all_data.

    Parameters
    ----------
    all_data : dict — keyed by date_key, values are data dicts from data_loader

    Returns
    -------
    dict keyed by date_key, values are risk result dicts
    """
    ordered_keys = ["Nov17", "Nov18", "Nov19", "Nov20", "Current"]
    results = {}
    prev = None
    for key in ordered_keys:
        if key in all_data:
            results[key] = compute_risk(all_data[key], prev)
            prev = all_data[key]
    return results
