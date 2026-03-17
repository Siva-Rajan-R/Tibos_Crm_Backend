import pandas as pd

def safe_date(value, fmt="%Y-%m-%d"):
    if value is None:
        return None

    if isinstance(value, str):
        value = value.strip()
        if value == "":
            return None

    try:
        ts = pd.to_datetime(value, errors="coerce")
        if pd.isna(ts):
            return None
        return ts.strftime(fmt)
    except Exception:
        return None