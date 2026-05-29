import sys
import sqlite3
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent.parent))

from config import DATABASE_FILE, REPORTS_DIR

OUTPUT_FILE = REPORTS_DIR / "PHASE_5_SUM_ENGINE.xlsx"


def digit_sum(number):
    return sum(int(x) for x in str(number).zfill(3))


def load_data():
    conn = sqlite3.connect(DATABASE_FILE)

    df = pd.read_sql_query(
        "SELECT draw_date, draw_type, number, box FROM draws",
        conn
    )

    conn.close()

    df["draw_date"] = pd.to_datetime(df["draw_date"])
    df["number"] = df["number"].astype(str).str.zfill(3)
    df["sum"] = df["number"].apply(digit_sum)

    return df


def sum_frequency(df):
    return (
        df.groupby("sum")
        .size()
        .reset_index(name="Hits")
        .sort_values("Hits", ascending=False)
    )


def sum_by_draw(df):
    return (
        df.groupby(["draw_type", "sum"])
        .size()
        .reset_index(name="Hits")
        .sort_values(["draw_type", "Hits"], ascending=[True, False])
    )


def recent_sum(df, last_n):
    recent = df.sort_values("draw_date").tail(last_n)

    return (
        recent.groupby("sum")
        .size()
        .reset_index(name=f"Hits Last {last_n}")
        .sort_values(f"Hits Last {last_n}", ascending=False)
    )


def sum_skip_report(df):
    df = df.sort_values(["draw_date", "draw_type"]).reset_index(drop=True)

    df["draw_index"] = df.index + 1

    latest = df["draw_index"].max()

    report = (
        df.groupby("sum")
        .agg(
            Last_Date=("draw_date", "max"),
            Last_Index=("draw_index", "max"),
        )
        .reset_index()
    )

    report["Current Skip"] = latest - report["Last_Index"]

    return report.sort_values("Current Skip", ascending=False)


def main():
    print("Loading data...")

    df = load_data()

    sum_freq = sum_frequency(df)
    sum_draw = sum_by_draw(df)

    recent_30 = recent_sum(df, 30)
    recent_60 = recent_sum(df, 60)
    recent_100 = recent_sum(df, 100)
    recent_200 = recent_sum(df, 200)

    skip_report = sum_skip_report(df)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
        sum_freq.to_excel(writer, sheet_name="Sum Frequency", index=False)
        sum_draw.to_excel(writer, sheet_name="Sum By Draw", index=False)
        recent_30.to_excel(writer, sheet_name="Recent 30", index=False)
        recent_60.to_excel(writer, sheet_name="Recent 60", index=False)
        recent_100.to_excel(writer, sheet_name="Recent 100", index=False)
        recent_200.to_excel(writer, sheet_name="Recent 200", index=False)
        skip_report.to_excel(writer, sheet_name="Sum Skip Report", index=False)

    print("\nPHASE 5 COMPLETE")
    print("Rows:", len(df))
    print("Report:", OUTPUT_FILE)

    print("\nTop 15 Sums:")
    print(sum_freq.head(15).to_string(index=False))

    print("\nTop 15 Recent 100 Sums:")
    print(recent_100.head(15).to_string(index=False))


if __name__ == "__main__":
    main()