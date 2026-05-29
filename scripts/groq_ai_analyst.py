import os
import sys
import sqlite3
from pathlib import Path

import pandas as pd
from groq import Groq
from dotenv import load_dotenv

# ==========================
# PATH SETUP
# ==========================
ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

from config import DATABASE_FILE
from scripts.load_settings import (
    GROQ_MODEL,
    GROQ_MAX_TOKENS,
    GROQ_TEMPERATURE,
)

# ==========================
# LOAD ENVIRONMENT VARIABLES
# ==========================
load_dotenv(ROOT / ".env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError(
        "GROQ_API_KEY not found. Create a .env file and add:\n"
        "GROQ_API_KEY=your_key_here"
    )

# ==========================
# PATHS
# ==========================
REPORTS_DIR = ROOT / "data" / "reports"
INPUT_FILE = REPORTS_DIR / "MASTER_FINAL_REPORT.xlsx"
OUTPUT_FILE = REPORTS_DIR / "PHASE_13_GROQ_AI_ANALYSIS.txt"

if not INPUT_FILE.exists():
    raise FileNotFoundError(
        f"Report not found:\n{INPUT_FILE}\n\nRun Phase 12 first."
    )

# ==========================
# DATABASE SUMMARY
# ==========================
conn = sqlite3.connect(DATABASE_FILE)

db_summary = pd.read_sql_query("""
SELECT
    COUNT(*) AS total_draws,
    MIN(draw_date) AS first_draw_date,
    MAX(draw_date) AS latest_draw_date
FROM draws
""", conn)

year_counts = pd.read_sql_query("""
SELECT
    substr(draw_date, 1, 4) AS year,
    COUNT(*) AS draws
FROM draws
GROUP BY year
ORDER BY year
""", conn)

draw_type_counts = pd.read_sql_query("""
SELECT
    draw_type,
    COUNT(*) AS draws
FROM draws
GROUP BY draw_type
ORDER BY draw_type
""", conn)

conn.close()

# ==========================
# LOAD REPORT DATA
# ==========================
master = pd.read_excel(INPUT_FILE, sheet_name="Top_25_Master")
candidates = pd.read_excel(INPUT_FILE, sheet_name="Top_25_Candidates")
digits = pd.read_excel(INPUT_FILE, sheet_name="Hot_Digits").head(10)
pairs = pd.read_excel(INPUT_FILE, sheet_name="Hot_Pairs").head(10)
sums = pd.read_excel(INPUT_FILE, sheet_name="Hot_Sums").head(10)

# Keep prompt smaller for free Groq usage
master_top = master.head(10)
candidates_top = candidates.head(10)

# ==========================
# AI PROMPT
# ==========================
prompt = f"""
You are an advanced lottery analytics assistant.

Important:
- Do NOT claim guaranteed wins.
- Lottery outcomes are random.
- Only discuss historical patterns and trends.
- Do NOT say the dataset has only a few draws if the database summary says otherwise.

DATABASE SUMMARY:
{db_summary.to_string(index=False)}

YEAR COUNTS:
{year_counts.to_string(index=False)}

DRAW TYPE COUNTS:
{draw_type_counts.to_string(index=False)}

TOP MASTER PICKS:
{master_top.to_string(index=False)}

TOP TREND CANDIDATES:
{candidates_top.to_string(index=False)}

HOT DIGITS:
{digits.to_string(index=False)}

HOT PAIRS:
{pairs.to_string(index=False)}

HOT SUMS:
{sums.to_string(index=False)}

Provide a concise professional analytics report with:

1. Executive Summary
2. Top 10 Strongest Box Numbers
3. Top 10 Aggressive / Trend-Based Candidates
4. Strongest Digit Clusters
5. Strongest Pair Clusters
6. Strongest Sum Ranges
7. Midday vs Evening Considerations
8. Risk Warning
9. Final Observations

Keep the report practical and not too long.
"""

# ==========================
# GROQ CLIENT + CALL
# ==========================
client = Groq(api_key=GROQ_API_KEY)

response = client.chat.completions.create(
    model=GROQ_MODEL,
    messages=[
        {
            "role": "system",
            "content": (
                "You are a professional lottery analytics assistant. "
                "You analyze historical data and trends but never claim certainty."
            ),
        },
        {
            "role": "user",
            "content": prompt,
        },
    ],
    temperature=GROQ_TEMPERATURE,
    max_tokens=GROQ_MAX_TOKENS,
)

analysis = response.choices[0].message.content

# ==========================
# SAVE REPORT
# ==========================
OUTPUT_FILE.write_text(analysis, encoding="utf-8")

print("\n====================================")
print("PHASE 13 COMPLETE")
print("====================================")
print("Model:", GROQ_MODEL)
print("Max Tokens:", GROQ_MAX_TOKENS)
print("Temperature:", GROQ_TEMPERATURE)
print("Saved Analysis:")
print(OUTPUT_FILE)
print("====================================\n")

print(analysis)