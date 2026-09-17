import math

def compute_risk_severity(rsl_diff: float) -> dict:
    """
    Primary risk severity, based exclusively on |RSL DIFF|.
    Matches the exact thresholds and absolute-value convention already
    used in fh_utils.py's compute_rsl_diff() elsewhere in the app.
    """
    if rsl_diff is None or (isinstance(rsl_diff, float) and math.isnan(rsl_diff)):
        return {"risk_level": "UNKNOWN", "risk_points": None}

    abs_diff = abs(rsl_diff)

    if abs_diff < 5:
        return {"risk_level": "LOW", "risk_points": 0}
    elif abs_diff < 10:
        return {"risk_level": "MEDIUM", "risk_points": 1}
    else:
        return {"risk_level": "HIGH", "risk_points": 2}