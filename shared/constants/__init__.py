"""Shared constants for Marketing OS v4."""

import json
from pathlib import Path

_CONSTANTS_DIR = Path(__file__).parent


def load_stop_words() -> dict:
    """Load stop words from JSON file."""
    path = _CONSTANTS_DIR / "stop_words.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# Load on import for convenience
STOP_WORDS = load_stop_words()