import json
from pathlib import Path

SETTINGS_PATH = Path(__file__).parent / "settings.json"

_default = {"currency": "$"}


def _ensure():
    if not SETTINGS_PATH.exists():
        SETTINGS_PATH.write_text(json.dumps(_default))


def get_currency() -> str:
    _ensure()
    data = json.loads(SETTINGS_PATH.read_text())
    return data.get("currency", "$")


def set_currency(symbol: str):
    _ensure()
    data = json.loads(SETTINGS_PATH.read_text())
    data["currency"] = symbol
    SETTINGS_PATH.write_text(json.dumps(data))
