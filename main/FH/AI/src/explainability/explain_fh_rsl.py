import shap
import pandas as pd

FEATURE_LABELS = {
    "RSL DIFF": "the signal difference from reference (RSL DIFF)",
    "Max RSL": "the received signal level (Max RSL)",
    "RSL REF": "the reference signal level (RSL REF)",
    "Max RSL_was_sentinel": "a missing/unreliable signal reading",
}

def explain_prediction(model, row_features: pd.Series, feature_cols: list, top_n: int = 2) -> str:
    """Generate a human-readable explanation for one row's prediction."""
    explainer = shap.TreeExplainer(model)
    X_row = row_features[feature_cols].to_frame().T
    shap_vals = explainer.shap_values(X_row)  # shape (1, n_features, n_classes)

    predicted_class = model.predict(X_row)[0]
    class_idx = list(model.classes_).index(predicted_class)

    contributions = pd.Series(
        shap_vals[0, :, class_idx], index=feature_cols
    ).sort_values(ascending=False)

    top_features = contributions.head(top_n)
    reasons = []
    for feat, value in top_features.items():
        if value > 0:  # only mention features that pushed toward this prediction
            label = FEATURE_LABELS.get(feat, feat)
            actual_value = row_features[feat]
            reasons.append(f"{label} (value: {round(actual_value, 2)})")
    reason_text = " and ".join(reasons) if reasons else "a combination of factors"
    return f"Predicted status: {predicted_class}. Main driver(s): {reason_text}."