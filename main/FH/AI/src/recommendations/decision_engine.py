import pandas as pd
from recommendations.risk_severity import compute_risk_severity
from recommendations.diagnosis import build_diagnosis


def compute_overall_risk(row: dict) -> dict:
    """
    New decision engine: risk severity comes ONLY from RSL DIFF.
    All other data (Sanity, fade margin, RTWP, weather later) is
    diagnostic evidence only — it never changes risk_level.
    """
    rsl_diff = row.get("RSL DIFF")
    severity = compute_risk_severity(rsl_diff)
    diagnosis = build_diagnosis(row)

    return {
        "risk_level": severity["risk_level"],
        "risk_points": severity["risk_points"],
        "raisons": "; ".join(diagnosis["raisons"]),
        "causes_possibles": "; ".join(diagnosis["causes_possibles"]),
    }