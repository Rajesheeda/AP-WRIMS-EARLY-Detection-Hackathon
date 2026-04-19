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
    """
    # 1. Surge points
    cur_inflow = current.get("pincha_inflow", 0) or current.get("annamayya_inflow", 0)
    prev_inflow = previous.get("pincha_inflow", 0) or previous.get("annamayya_inflow", 0) if previous else 0
    if prev_inflow > 0:
        surge_rate = (cur_inflow - prev_inflow) / prev_inflow
        surge_pts = min(surge_rate, 1.0) * 25.0 if surge_rate > 0 else 0.0
    else:
        surge_pts = 0.0

    # 2. Imbalance points
    outflow = current.get("annamayya_outflow", 0)
    inflow = current.get("annamayya_inflow", 0)
    if inflow > 1000 and (outflow is None or outflow < 10):
        # Dam cannot release — extreme backing up
        imbal_pts = 18.0
    elif outflow > inflow and inflow > 0:
        # outflow exceeding inflow = reverse pressure
        ratio = (outflow - inflow) / outflow
        imbal_pts = min(ratio, 1.0) * 20.0
    elif inflow == 0 and outflow == 0:
        imbal_pts = 0.0
    else:
        imbal_pts = 0.0

    # 3. Soil moisture
    soil = current.get("soil_moisture_100cm", 0.0)
    soil_pts = (soil / 100.0) * 25.0

    # 4. Rainfall points
    actual = current.get("rainfall_actual", 0.0)
    normal = current.get("rainfall_normal", 0.0)
    if normal > 0:
        rain_pts = (min(actual / normal, 5.0) / 5.0) * 20.0
    else:
        rain_pts = 0.0

    # 5. Dam offline / sensor penalty
    sensor_dead = current.get("annamayya_sensor_dead", False)
    if sensor_dead:
        sensor_pts = 10.0
    elif previous and inflow > 0 and inflow == previous.get("annamayya_inflow", -1):
        sensor_pts = 5.0
    else:
        sensor_pts = 0.0

    # 6. Cascade bonus
    cascade_bonus = 20.0 if (surge_pts > 0 and imbal_pts > 0) else 0.0

    # 7. Tank bonus
    tank = current.get("mi_tank_fill_pct", 0)
    if tank >= 80:
        tank_bonus = 12.0
    elif tank >= 70:
        tank_bonus = 6.0
    else:
        tank_bonus = 0.0

    # 8. Score calculation
    score = soil_pts + surge_pts + imbal_pts + rain_pts + sensor_pts + cascade_bonus + tank_bonus
    score = _clamp(score, 0.0, 100.0)

    # Risk level
    level = "LOW"
    for lvl, (lo, hi) in THRESHOLDS.items():
        if lo <= score < hi:
            level = lvl
            break

    # Confidence
    confidence = 95.0
    if sensor_dead:
        confidence -= 20.0
    if previous is None:
        confidence -= 15.0
    if cur_inflow == 0:
        confidence -= 10.0
    confidence = round(_clamp(confidence, 0.0, 100.0), 1)

    time_to_failure = _estimate_tte(score, level, surge_pts/25.0 if surge_pts else 0)

    # Top factors
    factors = [
        ("Soil Moisture (100cm)", round(soil_pts, 1)),
        ("Inflow Surge Rate", round(surge_pts, 1)),
        ("Discharge Imbalance", round(imbal_pts, 1)),
        ("Rainfall Anomaly", round(rain_pts, 1)),
        ("Dam Offline Penalty", round(sensor_pts, 1))
    ]
    if cascade_bonus > 0:
        factors.append(("Cascade Risk Bonus", round(cascade_bonus, 1)))
    if tank_bonus > 0:
        factors.append(("MI Tank Saturation Bonus", round(tank_bonus, 1)))
        
    top_factors = sorted(factors, key=lambda x: x[1], reverse=True)

    return {
        "score": round(score, 2),
        "level": level,
        "confidence": confidence,
        "time_to_failure": time_to_failure,
        "top_factors": top_factors,
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
