import sys
import sqlite3
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent.parent))

from config import DATABASE_FILE, REPORTS_DIR

OUTPUT_FILE = REPORTS_DIR / "PHASE_8_SKIP_TRACKER.xlsx"


def load_data():
    conn = sqlite3.connect(DATABASE_FILE)

    df = pd.read_sql_query(
        "SELECT draw_date, draw_type, number, box FROM draws",
        conn
    )

    conn.close()

    df["draw_date"] = pd.to_datetime(df["draw_date"])
    df = df.sort_values(["draw_date", "draw_type"]).reset_index(drop=True)

    df["draw_index"] = df.index + 1

    return df


def build_skip_report(df):
    latest_index = df["draw_index"].max()

    rows = []

    for box, group in df.groupby("box"):
        indexes = sorted(group["draw_index"].tolist())

        skips = []

        for i in range(1, len(indexes)):
            skips.append(indexes[i] - indexes[i - 1])

        avg_skip = round(sum(skips) / len(skips), 2) if skips else 0
        max_skip = max(skips) if skips else 0

        last_seen_index = indexes[-1]
        current_skip = latest_index - last_seen_index

        rows.append({
            "Box": box,
            "Hits": len(indexes),
            "Current Skip": current_skip,
            "Average Skip": avg_skip,
            "Max Skip": max_skip,
            "Last Seen Date": group["draw_date"].max().date(),
        })

    report = pd.DataFrame(rows)

    return report.sort_values(
        ["Current Skip", "Hits"],
        ascending=[False, False]
    )


def main():
    print("Loading data...")

    df = load_data()

    print("Building skip tracker...")

    report = build_skip_report(df)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
        report.to_excel(writer, sheet_name="Skip Tracker", index=False)

    print("\nPHASE 8 COMPLETE")
    print("Report:", OUTPUT_FILE)

    print("\nTop 20 Most Overdue Boxes:")
    print(report.head(20).to_string(index=False))


if __name__ == "__main__":
    main()