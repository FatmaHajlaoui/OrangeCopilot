import shap
import pandas as pd

FEATURE_LABELS = {
    "RSL (Min)": "the minimum received signal level",
    "RSL (Max)": "the maximum received signal level",
    "RSL (Avg)": "the average received signal level",
    "rsl_range": "signal instability (RSL range)",
    "UAS": "unavailable seconds (UAS)",
    "SEP": "severely errored periods (SEP)",
    "SES": "severely errored seconds (SES)",
    "ES": "errored seconds (ES)",
    "BBE": "background block errors (BBE)",
    "OFS": "out-of-frame seconds (OFS)",
    "RSL (Min)_was_sentinel": "a missing/unreliable minimum RSL reading",
    "RSL (Max)_was_sentinel": "a missing/unreliable maximum RSL reading",
    "RSL (Avg)_was_sentinel": "a missing/unreliable average RSL reading",
}

def explain_prediction(model, row_features: pd.Series, feature_cols: list, top_n: int = 3) -> str:
    """Generate a human-readable explanation for one row's Sanity prediction."""
    explainer = shap.TreeExplainer(model)
    X_row = row_features[feature_cols].to_frame().T
    shap_vals = explainer.shap_values(X_row)

    predicted_class = model.predict(X_row)[0]
    class_idx = list(model.classes_).index(predicted_class)

    contributions = pd.Series(
        shap_vals[0, :, class_idx], index=feature_cols
    ).sort_values(ascending=False)

    top_features = contributions.head(top_n)
    reasons = []
    for feat, value in top_features.items():
        if value > 0:
            label = FEATURE_LABELS.get(feat, feat)
            actual_value = row_features[feat]
            reasons.append(f"{label} (value: {round(actual_value, 2)})")

    reason_text = " and ".join(reasons) if reasons else "a combination of factors"
    return f"Predicted sanity: {predicted_class}. Main driver(s): {reason_text}."