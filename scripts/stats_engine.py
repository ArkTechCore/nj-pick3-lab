import sys
import sqlite3
from pathlib import Path
from collections import Counter

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent.parent))

from config import DATABASE_FILE, REPORTS_DIR

OUTPUT_FILE = REPORTS_DIR / "PHASE_3_STATISTICS.xlsx"


def load_data():
    conn = sqlite3.connect(DATABASE_FILE)

    df = pd.read_sql_query(
        "SELECT draw_date, draw_type, number, box FROM draws",
        conn
    )

    conn.close()

    return df


def digit_frequency(df):
    digits = []

    for n in df["number"]:
        digits.extend(list(str(n).zfill(3)))

    freq = Counter(digits)

    return (
        pd.DataFrame(freq.items(), columns=["Digit", "Hits"])
        .sort_values("Hits", ascending=False)
    )


def position_frequency(df):
    rows = []

    for n in df["number"]:
        n = str(n).zfill(3)

        rows.append(("Position1", n[0]))
        rows.append(("Position2", n[1]))
        rows.append(("Position3", n[2]))

    pos_df = pd.DataFrame(rows, columns=["Position", "Digit"])

    return (
        pos_df.groupby(["Position", "Digit"])
        .size()
        .reset_index(name="Hits")
        .sort_values(["Position", "Hits"], ascending=[True, False])
    )


def box_frequency(df):
    return (
        df.groupby("box")
        .size()
        .reset_index(name="Hits")
        .sort_values("Hits", ascending=False)
    )


def midday_evening_stats(df):
    return (
        df.groupby("draw_type")
        .size()
        .reset_index(name="Draw Count")
    )


def hot_cold_digits(df):
    digit_stats = digit_frequency(df)

    hot = digit_stats.head(5)
    cold = digit_stats.tail(5)

    return hot, cold


def main():
    print("Loading data...")

    df = load_data()

    digit_stats = digit_frequency(df)
    position_stats = position_frequency(df)
    box_stats = box_frequency(df)
    draw_stats = midday_evening_stats(df)

    hot, cold = hot_cold_digits(df)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
        digit_stats.to_excel(writer, sheet_name="Digit Frequency", index=False)
        position_stats.to_excel(writer, sheet_name="Position Frequency", index=False)
        box_stats.to_excel(writer, sheet_name="Box Frequency", index=False)
        draw_stats.to_excel(writer, sheet_name="Midday Evening", index=False)
        hot.to_excel(writer, sheet_name="Hot Digits", index=False)
        cold.to_excel(writer, sheet_name="Cold Digits", index=False)

    print("\nPHASE 3 COMPLETE")
    print("Rows:", len(df))
    print("Report:", OUTPUT_FILE)

    print("\nTop 10 Digits")
    print(digit_stats.head(10).to_string(index=False))

    print("\nTop 10 Boxes")
    print(box_stats.head(10).to_string(index=False))


if __name__ == "__main__":
    main()