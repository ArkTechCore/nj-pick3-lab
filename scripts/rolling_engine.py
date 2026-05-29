import sys
import sqlite3
import itertools
from pathlib import Path
from collections import Counter

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent.parent))

from config import DATABASE_FILE, REPORTS_DIR

OUTPUT_FILE = REPORTS_DIR / "PHASE_7_ROLLING_ENGINE.xlsx"

WINDOWS = [30, 60, 100, 200]


def load_data():
    conn = sqlite3.connect(DATABASE_FILE)
    df = pd.read_sql_query(
        "SELECT draw_date, draw_type, number, box FROM draws",
        conn
    )
    conn.close()

    df["draw_date"] = pd.to_datetime(df["draw_date"])
    df["number"] = df["number"].astype(str).str.zfill(3)
    df = df.sort_values(["draw_date", "draw_type"]).reset_index(drop=True)
    return df


def digit_sum(n):
    return sum(int(x) for x in str(n).zfill(3))


def get_pairs(n):
    digits = list(str(n).zfill(3))
    return ["".join(sorted(p)) for p in itertools.combinations(digits, 2)]


def digit_report(df, window):
    digits = Counter("".join(df["number"].tolist()))
    return (
        pd.DataFrame(digits.items(), columns=["Digit", f"Hits Last {window}"])
        .sort_values(f"Hits Last {window}", ascending=False)
    )


def box_report(df, window):
    return (
        df.groupby("box")
        .size()
        .reset_index(name=f"Hits Last {window}")
        .sort_values(f"Hits Last {window}", ascending=False)
    )


def pair_report(df, window):
    pairs = []
    for n in df["number"]:
        pairs.extend(get_pairs(n))

    counts = Counter(pairs)

    return (
        pd.DataFrame(counts.items(), columns=["Pair", f"Hits Last {window}"])
        .sort_values(f"Hits Last {window}", ascending=False)
    )


def sum_report(df, window):
    temp = df.copy()
    temp["sum"] = temp["number"].apply(digit_sum)

    return (
        temp.groupby("sum")
        .size()
        .reset_index(name=f"Hits Last {window}")
        .sort_values(f"Hits Last {window}", ascending=False)
    )


def build_window(df, window):
    recent = df.tail(window)

    return {
        f"Digits {window}": digit_report(recent, window),
        f"Boxes {window}": box_report(recent, window),
        f"Pairs {window}": pair_report(recent, window),
        f"Sums {window}": sum_report(recent, window),
    }


def main():
    print("Loading data...")
    df = load_data()

    all_sheets = {}

    for window in WINDOWS:
        print(f"Building rolling window {window}...")
        all_sheets.update(build_window(df, window))

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
        for sheet_name, sheet_df in all_sheets.items():
            sheet_df.to_excel(writer, sheet_name=sheet_name[:31], index=False)

    print("\nPHASE 7 COMPLETE")
    print("Report:", OUTPUT_FILE)

    print("\nTop Rolling 100 Digits:")
    print(all_sheets["Digits 100"].head(10).to_string(index=False))

    print("\nTop Rolling 100 Boxes:")
    print(all_sheets["Boxes 100"].head(10).to_string(index=False))

    print("\nTop Rolling 100 Pairs:")
    print(all_sheets["Pairs 100"].head(10).to_string(index=False))

    print("\nTop Rolling 100 Sums:")
    print(all_sheets["Sums 100"].head(10).to_string(index=False))


if __name__ == "__main__":
    main()