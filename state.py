import json
import os

STATE_FILE = "seen_state.json"


def load_last_seen():
    if not os.path.exists(STATE_FILE):
        return None
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f).get("last_seen_nro_parte")


def save_last_seen(nro_parte: int):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump({"last_seen_nro_parte": nro_parte}, f)
