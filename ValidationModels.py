from datetime import datetime

def normalize_date(v: str) -> str:
    for fmt in ("%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(v, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    raise ValueError(f"Invalid date '{v}'. Use DD-MM-YYYY or YYYY-MM-DD.")