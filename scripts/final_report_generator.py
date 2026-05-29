from pathlib import Path
import pandas as pd

BASE = Path("data/reports")

OUTPUT = BASE / "MASTER_FINAL_REPORT.xlsx"

files = {
    "Master_Scoring":
        BASE / "PHASE_11_MASTER_SCORING.xlsx",

    "Candidates":
        BASE / "PHASE_11_5_CANDIDATES.xlsx",

    "Statistics":
        BASE / "PHASE_3_STATISTICS.xlsx",

    "Pairs":
        BASE / "PHASE_4_PAIR_ENGINE.xlsx",

    "Sums":
        BASE / "PHASE_5_SUM_ENGINE.xlsx",

    "Patterns":
        BASE / "PHASE_6_PATTERN_ENGINE.xlsx",

    "Rolling":
        BASE / "PHASE_7_ROLLING_ENGINE.xlsx",

    "SkipTracker":
        BASE / "PHASE_8_SKIP_TRACKER.xlsx",

    "Midday":
        BASE / "PHASE_9_MIDDAY_MODEL.xlsx",

    "Evening":
        BASE / "PHASE_10_EVENING_MODEL.xlsx",
}

with pd.ExcelWriter(OUTPUT, engine="openpyxl") as writer:

    # Top 25 Master Picks
    master = pd.read_excel(
        files["Master_Scoring"],
        sheet_name="Top 100 Plays"
    )

    master.head(25).to_excel(
        writer,
        sheet_name="Top_25_Master",
        index=False
    )

    # Top 25 Candidates
    candidates = pd.read_excel(
        files["Candidates"],
        sheet_name="Top 25 Candidates"
    )

    candidates.to_excel(
        writer,
        sheet_name="Top_25_Candidates",
        index=False
    )

    # Hot digits
    digits = pd.read_excel(
        files["Statistics"],
        sheet_name="Digit Frequency"
    )

    digits.to_excel(
        writer,
        sheet_name="Hot_Digits",
        index=False
    )

    # Hot pairs
    pairs = pd.read_excel(
        files["Pairs"],
        sheet_name="Pair Frequency"
    )

    pairs.to_excel(
        writer,
        sheet_name="Hot_Pairs",
        index=False
    )

    # Hot sums
    sums = pd.read_excel(
        files["Sums"],
        sheet_name="Sum Frequency"
    )

    sums.to_excel(
        writer,
        sheet_name="Hot_Sums",
        index=False
    )

    # Rolling 100
    rolling_pairs = pd.read_excel(
        files["Rolling"],
        sheet_name="Pairs 100"
    )

    rolling_pairs.to_excel(
        writer,
        sheet_name="Rolling_100_Pairs",
        index=False
    )

    # Skip tracker
    skip = pd.read_excel(
        files["SkipTracker"],
        sheet_name="Skip Tracker"
    )

    skip.to_excel(
        writer,
        sheet_name="Skip_Tracker",
        index=False
    )

    # Midday
    midday = pd.read_excel(
        files["Midday"],
        sheet_name="Hot Pairs"
    )

    midday.to_excel(
        writer,
        sheet_name="Midday_Hot_Pairs",
        index=False
    )

    # Evening
    evening = pd.read_excel(
        files["Evening"],
        sheet_name="Hot Pairs"
    )

    evening.to_excel(
        writer,
        sheet_name="Evening_Hot_Pairs",
        index=False
    )

print("\nFINAL REPORT CREATED")
print(OUTPUT)