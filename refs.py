import json
import os
from paths import app_path

COUNTER_FILE = app_path("counter.json")


def next_reference(prefix: str, d) -> str:
    """('SGC/EXP', date) -> 'SGC/EXP/2026-10-26/0000001' (counts up each call)."""
    data = {}
    if os.path.exists(COUNTER_FILE):
        try:
            with open(COUNTER_FILE) as f:
                data = json.load(f)
        except Exception:
            data = {}
    n = data.get(prefix, 0) + 1
    data[prefix] = n
    with open(COUNTER_FILE, "w") as f:
        json.dump(data, f)
    return f"{prefix}/{d:%Y-%m-%d}/{n:07d}"