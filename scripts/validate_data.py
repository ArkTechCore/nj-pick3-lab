import sys
import sqlite3
from pathlib import Path
from datetime import date

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent.parent))

from config import DATABASE_FILE, REPORTS_DIR

OUTPUT_FILE = REPORTS_DIR / "PHASE_2_VALIDATION_REPORT.xlsx"


def load_draws():
    conn = sqlite3.connect(DATABASE_FILE)
    df = pd.read_sql_query("SELECT * FROM draws", conn)
    conn.close()

    df["draw_date"] = pd.to_datetime(df["draw_date"])
    df["year"] = df["draw_date"].dt.year

    return df


def validate_rows(df):
    checks = []

    checks.append({"Check": "Total rows", "Result": len(df)})
    checks.append({"Check": "Duplicate date + draw_type", "Result": df.duplicated(["draw_date", "draw_type"]).sum()})
    checks.append({"Check": "Invalid number length", "Result": (~df["number"].astype(str).str.match(r"^\d{3}$")).sum()})
    checks.append({"Check": "Invalid box length", "Result": (~df["box"].astype(str).str.match(r"^\d{3}$")).sum()})

    return pd.DataFrame(checks)


def counts_by_year_draw(df):
    return (
        df.groupby(["year", "draw_type"])
        .size()
        .reset_index(name="rows")
        .sort_values(["year", "draw_type"])
    )


def missing_draws(df):
    rows = []

    for year in sorted(df["year"].unique()):
        start = date(year, 1, 1)
        end = date(year, 12, 31)

        all_dates = pd.date_range(start, end)

        for d in all_dates:
            for draw_type in ["Midday", "Evening"]:
                exists = (
                    (df["draw_date"].dt.date == d.date())
                    & (df["draw_type"] == draw_type)
                ).any()

                if not exists:
                    rows.append({
                        "missing_date": d.date().isoformat(),
                        "draw_type": draw_type,
                        "year": year
                    })

    return pd.DataFrame(rows)


def duplicate_rows(df):
    return df[df.duplicated(["draw_date", "draw_type"], keep=False)].sort_values(["draw_date", "draw_type"])


def save_report(df, summary, counts, missing, duplicates):
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
        summary.to_excel(writer, sheet_name="Summary Checks", index=False)
        counts.to_excel(writer, sheet_name="Counts By Year Draw", index=False)
        missing.to_excel(writer, sheet_name="Missing Draws", index=False)
        duplicates.to_excel(writer, sheet_name="Duplicates", index=False)
        df.to_excel(writer, sheet_name="All Draws", index=False)


def main():
    print("Loading database...")
    df = load_draws()

    print("Running validation...")
    summary = validate_rows(df)
    counts = counts_by_year_draw(df)
    missing = missing_draws(df)
    duplicates = duplicate_rows(df)

    save_report(df, summary, counts, missing, duplicates)

    print("\nPHASE 2 VALIDATION COMPLETE")
    print("Rows:", len(df))
    print("Missing draws:", len(missing))
    print("Duplicates:", len(duplicates))
    print("Report saved:", OUTPUT_FILE)


if __name__ == "__main__":
    main()