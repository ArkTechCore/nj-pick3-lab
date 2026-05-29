import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SETTINGS_FILE = ROOT / "settings.json"

with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
    SETTINGS = json.load(f)

START_YEAR = SETTINGS["start_year"]
END_YEAR = SETTINGS["end_year"]
ROLLING_WINDOWS = SETTINGS["rolling_windows"]
TOP_CANDIDATE_COUNT = SETTINGS["top_candidate_count"]

GROQ_MODEL = SETTINGS["groq_model"]
GROQ_MAX_TOKENS = SETTINGS["groq_max_tokens"]
GROQ_TEMPERATURE = SETTINGS["groq_temperature"]