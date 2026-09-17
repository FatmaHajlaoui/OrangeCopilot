import joblib
import pandas as pd
from pathlib import Path

AI_DIR = Path(__file__).resolve().parents[2]  # points to FH/AI/
MODELS_DIR = AI_DIR / "models"
PROCESSED_DIR = AI_DIR / "data" / "processed"

_fh_rsl_model = None
_sanity_model = None

FH_RSL_FEATURES = ["Max RSL", "RSL REF", "RSL DIFF", "Max RSL_was_sentinel"]
SANITY_FEATURES = [
    "RSL (Min)", "RSL (Max)", "RSL (Avg)", "rsl_range",
    "UAS", "SEP", "SES", "ES", "BBE", "OFS",
    "RSL (Min)_was_sentinel", "RSL (Max)_was_sentinel", "RSL (Avg)_was_sentinel",
]


def _load_models():
    global _fh_rsl_model, _sanity_model
    if _fh_rsl_model is None:
        _fh_rsl_model = joblib.load(MODELS_DIR / "fh_rsl_classifier.pkl")
    if _sanity_model is None:
        _sanity_model = joblib.load(MODELS_DIR / "sanity_classifier.pkl")


def predict_fh_rsl(max_rsl, rsl_ref, rsl_diff, max_rsl_was_sentinel=False):
    """Predict FH RSL link status from raw feature values."""
    _load_models()
    row = pd.DataFrame([{
        "Max RSL": max_rsl,
        "RSL REF": rsl_ref,
        "RSL DIFF": rsl_diff,
        "Max RSL_was_sentinel": max_rsl_was_sentinel,
    }])[FH_RSL_FEATURES]
    prediction = _fh_rsl_model.predict(row)[0]
    return {"status": prediction}


def predict_sanity(features: dict):
    """Predict Sanity classification. `features` must contain all SANITY_FEATURES keys."""
    _load_models()
    row = pd.DataFrame([features])[SANITY_FEATURES]
    prediction = _sanity_model.predict(row)[0]
    return {"sanity": prediction}


def get_network_risk_assessment():
    """Return the precomputed per-link risk assessment as a list of dicts."""
    df = pd.read_csv(PROCESSED_DIR / "network_risk_assessment_v3.csv")
    df = df.astype(object).where(df.notna(), None) # NaN -> None so jsonify works cleanly
    return df.to_dict(orient="records")


def get_risk_for_ip(ip: str):
    """Return the risk assessment for one specific IP, or None if not found."""
    df = pd.read_csv(PROCESSED_DIR / "network_risk_assessment_v3.csv")
    df = df.astype(object).where(df.notna(), None)
    row = df[df["IP"] == ip]
    if row.empty:
        return None
    return row.to_dict(orient="records")[0]