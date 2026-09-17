import pandas as pd
from pathlib import Path

# (row, column) positions confirmed fixed across 20 sampled files
FIELD_MAP = {
    "link_id":        (25, 0, "value_direct"),   # label in col0, value in col1
    "capacity":       (26, 0, "value_direct"),
    "length_m":       (25, 2, "value_direct"),   # label in col2, value in col3
    "calc_method":    (26, 2, "value_direct"),
    "band":           (35, 1, "end_ab"),         # label col1, values col2/col3
    "bandwidth_mhz":  (38, 1, "end_ab"),
    "polarisation":   (40, 1, "end_ab"),
    "antenna_type":   (42, 1, "end_ab"),
    "antenna_size_m": (43, 1, "end_ab"),
    "antenna_height_m": (44, 1, "end_ab"),
    "antenna_direction_deg": (45, 1, "end_ab"),
    "antenna_gain_db": (47, 1, "end_ab"),
    "tx_power_dbm":   (53, 1, "end_ab"),
    "tx_attenuator_db": (54, 1, "end_ab"),
    "rx_attenuator_db": (55, 1, "end_ab"),
    "modulation":     (56, 1, "end_ab"),
    "threshold_dbm":  (62, 1, "end_ab"),
    "main_rx_level_dbm": (65, 1, "end_ab"),
    "threshold_degradation_db": (67, 1, "end_ab"),
    "main_flat_fade_margin_db": (68, 1, "end_ab"),
}

def parse_mlo_file(filepath: Path) -> dict:
    """Parse one Atoll Link Reporter MLO file into a flat dict.
    Returns a dict with '_error' set if the file doesn't match expectations."""
    try:
        # use sheet position 0 instead of a fixed name — some files may not use "Feuil1"
        df = pd.read_excel(filepath, sheet_name=0, header=None)
    except Exception as e:
        return {"_file": filepath.name, "_error": f"read failed: {e}"}

    if df.shape[0] < 70 or df.shape[1] < 4:
        return {"_file": filepath.name, "_error": f"unexpected shape {df.shape}"}

    result = {"_file": filepath.name, "_error": None}

    for field_name, (row, label_col, mode) in FIELD_MAP.items():
        try:
            if mode == "value_direct":
                result[field_name] = df.iat[row, label_col + 1]
            elif mode == "end_ab":
                result[f"{field_name}_end_a"] = df.iat[row, label_col + 1]
                result[f"{field_name}_end_b"] = df.iat[row, label_col + 2]
        except Exception:
            result[field_name] = None

    return result