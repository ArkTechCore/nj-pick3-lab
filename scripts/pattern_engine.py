import sys
import sqlite3
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent.parent))

from config import DATABASE_FILE, REPORTS_DIR

OUTPUT_FILE = REPORTS_DIR / "PHASE_6_PATTERN_ENGINE.xlsx"


def load_data():
    conn = sqlite3.connect(DATABASE_FILE)

    df = pd.read_sql_query(
        "SELECT draw_date, draw_type, number FROM draws",
        conn
    )

    conn.close()

    df["number"] = df["number"].astype(str).str.zfill(3)

    return df


def odd_even_pattern(number):
    return "".join(
        "O" if int(d) % 2 else "E"
        for d in str(number)
    )


def high_low_pattern(number):
    return "".join(
        "H" if int(d) >= 5 else "L"
        for d in str(number)
    )


def number_type(number):
    unique = len(set(str(number)))

    if unique == 1:
        return "Triple"

    if unique == 2:
        return "Double"

    return "Single"


def build_patterns(df):
    df["OddEven"] = df["number"].apply(odd_even_pattern)
    df["HighLow"] = df["number"].apply(high_low_pattern)
    df["Type"] = df["number"].apply(number_type)

    return df


def frequency_report(df, column):
    return (
        df.groupby(column)
        .size()
        .reset_index(name="Hits")
        .sort_values("Hits", ascending=False)
    )


def recent_report(df, column, last_n):
    recent = df.tail(last_n)

    return (
        recent.groupby(column)
        .size()
        .reset_index(name=f"Hits Last {last_n}")
        .sort_values(f"Hits Last {last_n}", ascending=False)
    )


def main():
    print("Loading data...")

    df = load_data()

    print("Building patterns...")
    df = build_patterns(df)

    odd_even = frequency_report(df, "OddEven")
    high_low = frequency_report(df, "HighLow")
    type_report = frequency_report(df, "Type")

    recent_100_oe = recent_report(df, "OddEven", 100)
    recent_100_hl = recent_report(df, "HighLow", 100)
    recent_100_type = recent_report(df, "Type", 100)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
        odd_even.to_excel(writer, sheet_name="Odd Even", index=False)
        high_low.to_excel(writer, sheet_name="High Low", index=False)
        type_report.to_excel(writer, sheet_name="Number Type", index=False)

        recent_100_oe.to_excel(writer, sheet_name="Recent100 OddEven", index=False)
        recent_100_hl.to_excel(writer, sheet_name="Recent100 HighLow", index=False)
        recent_100_type.to_excel(writer, sheet_name="Recent100 Type", index=False)

        df.to_excel(writer, sheet_name="Pattern Data", index=False)

    print("\nPHASE 6 COMPLETE")
    print("Report:", OUTPUT_FILE)

    print("\nOdd/Even Patterns")
    print(odd_even.to_string(index=False))

    print("\nHigh/Low Patterns")
    print(high_low.to_string(index=False))

    print("\nSingles / Doubles / Triples")
    print(type_report.to_string(index=False))


if __name__ == "__main__":
    main()