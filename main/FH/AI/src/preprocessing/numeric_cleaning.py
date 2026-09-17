import re
import pandas as pd

def clean_numeric(value):
    """Convert a messy numeric string like '700,77 m', '-78,5 dBm', '41 Mbps'
    into a float. Returns None if it can't be parsed."""
    if pd.isna(value):
        return None
    if isinstance(value, (int, float)):
        return float(value)

    s = str(value).strip()

    # remove spaces used as thousands separators (e.g. "2 023,68")
    s = s.replace("\u00a0", " ")  # non-breaking space, sometimes used by Excel
    s = re.sub(r"(?<=\d) (?=\d)", "", s)  # remove spaces between digits

    # extract the numeric part: optional minus, digits, optional , or . decimal
    match = re.search(r"-?\d+(?:[.,]\d+)?", s)
    if not match:
        return None

    num_str = match.group(0).replace(",", ".")
    try:
        return float(num_str)
    except ValueError:
        return None


def extract_bandwidth_mhz(value):
    """Extract the true bandwidth from a channel code like
    'LK_38GHz_3.5MHz[-]' -> 3.5. Returns None if no MHz value found."""
    if pd.isna(value):
        return None
    s = str(value)
    match = re.search(r"(\d+(?:[.,]\d+)?)\s*MHz", s)
    if not match:
        return None
    return float(match.group(1).replace(",", "."))

def flag_and_clean_sentinels(df, columns, zero_is_sentinel=True, floor_threshold=-98.5):
    """For each column in `columns`, replace sentinel values (0 dBm and/or
    values at or below floor_threshold) with NaN, and add a companion
    boolean column '<col>_was_sentinel' recording where this happened.
    Returns a new DataFrame; does not modify the input in place."""
    df = df.copy()
    for col in columns:
        is_zero = (df[col] == 0) if zero_is_sentinel else pd.Series(False, index=df.index)
        is_floor = df[col] <= floor_threshold
        is_sentinel = is_zero | is_floor

        df[f"{col}_was_sentinel"] = is_sentinel
        df.loc[is_sentinel, col] = pd.NA
        df[col] = df[col].astype(float)

    return df