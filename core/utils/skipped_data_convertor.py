from datetime import date,timezone,timedelta,datetime
from pathlib import Path
import pandas as pd


def make_json_safe(obj):
    if isinstance(obj, dict):
        return {k: make_json_safe(v) for k, v in obj.items()}

    if isinstance(obj, (list, tuple, set)):
        return [make_json_safe(v) for v in obj]

    if hasattr(obj, "model_dump"):
        return make_json_safe(obj.model_dump())

    from datetime import datetime, date
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()

    try:
        import pandas as pd
        if isinstance(obj, pd.Timestamp):
            return obj.isoformat()
    except Exception:
        pass

    return str(obj)




def write_skipped_items_to_excel(skipped_items: list, prefix="skipped_orders"):
    if not skipped_items:
        return None

    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    output_dir = Path("skipped_reports")
    output_dir.mkdir(exist_ok=True)

    file_path = output_dir / f"{prefix}_{ts}.xlsx"

    # convert nested objects safely
    safe_items = [make_json_safe(item) for item in skipped_items]

    df = pd.DataFrame(safe_items)

    df.to_excel(file_path, index=False)

    return file_path.as_posix()