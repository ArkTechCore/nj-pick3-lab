import sys
import sqlite3
import itertools
from pathlib import Path
from collections import Counter

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent.parent))

from config import DATABASE_FILE, REPORTS_DIR

OUTPUT_FILE = REPORTS_DIR / "PHASE_4_PAIR_ENGINE.xlsx"


def load_data():
    conn = sqlite3.connect(DATABASE_FILE)

    df = pd.read_sql_query(
        "SELECT draw_date, draw_type, number, box FROM draws",
        conn
    )

    conn.close()

    df["draw_date"] = pd.to_datetime(df["draw_date"])
    df["number"] = df["number"].astype(str).str.zfill(3)

    return df


def get_pairs(number):
    digits = list(str(number).zfill(3))
    pairs = []

    for pair in itertools.combinations(digits, 2):
        pairs.append("".join(sorted(pair)))

    return pairs


def pair_frequency(df):
    rows = []

    for _, row in df.iterrows():
        pairs = get_pairs(row["number"])

        for pair in pairs:
            rows.append({
                "draw_date": row["draw_date"],
                "draw_type": row["draw_type"],
                "number": row["number"],
                "box": row["box"],
                "pair": pair,
            })

    pair_df = pd.DataFrame(rows)

    freq = (
        pair_df.groupby("pair")
        .size()
        .reset_index(name="Hits")
        .sort_values("Hits", ascending=False)
    )

    return pair_df, freq


def pair_by_draw_type(pair_df):
    return (
        pair_df.groupby(["draw_type", "pair"])
        .size()
        .reset_index(name="Hits")
        .sort_values(["draw_type", "Hits"], ascending=[True, False])
    )


def pair_recent(pair_df, last_n):
    recent_draws = (
        pair_df[["draw_date", "draw_type", "number"]]
        .drop_duplicates()
        .sort_values(["draw_date", "draw_type"])
        .tail(last_n)
    )

    recent_pair_df = pair_df.merge(
        recent_draws,
        on=["draw_date", "draw_type", "number"],
        how="inner"
    )

    return (
        recent_pair_df.groupby("pair")
        .size()
        .reset_index(name=f"Hits Last {last_n}")
        .sort_values(f"Hits Last {last_n}", ascending=False)
    )


def pair_skip_report(pair_df):
    draw_order = (
        pair_df[["draw_date", "draw_type", "number"]]
        .drop_duplicates()
        .sort_values(["draw_date", "draw_type"])
        .reset_index(drop=True)
    )

    draw_order["draw_index"] = draw_order.index + 1

    pair_with_index = pair_df.merge(
        draw_order,
        on=["draw_date", "draw_type", "number"],
        how="left"
    )

    latest_index = draw_order["draw_index"].max()

    last_seen = (
        pair_with_index.groupby("pair")
        .agg(
            Last_Seen_Date=("draw_date", "max"),
            Last_Seen_Index=("draw_index", "max"),
            Last_Number=("number", "last"),
        )
        .reset_index()
    )

    last_seen["Current Skip"] = latest_index - last_seen["Last_Seen_Index"]

    return last_seen.sort_values("Current Skip", ascending=False)


def main():
    print("Loading data...")
    df = load_data()

    print("Building pair frequency...")
    pair_df, pair_freq = pair_frequency(df)

    print("Building pair by draw type...")
    by_draw = pair_by_draw_type(pair_df)

    print("Building recent pair reports...")
    recent_30 = pair_recent(pair_df, 30)
    recent_60 = pair_recent(pair_df, 60)
    recent_100 = pair_recent(pair_df, 100)
    recent_200 = pair_recent(pair_df, 200)

    print("Building pair skip report...")
    skip_report = pair_skip_report(pair_df)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
        pair_freq.to_excel(writer, sheet_name="Pair Frequency", index=False)
        by_draw.to_excel(writer, sheet_name="Pair By Draw Type", index=False)
        recent_30.to_excel(writer, sheet_name="Recent 30", index=False)
        recent_60.to_excel(writer, sheet_name="Recent 60", index=False)
        recent_100.to_excel(writer, sheet_name="Recent 100", index=False)
        recent_200.to_excel(writer, sheet_name="Recent 200", index=False)
        skip_report.to_excel(writer, sheet_name="Pair Skip Report", index=False)
        pair_df.to_excel(writer, sheet_name="Pair Raw Data", index=False)

    print("\nPHASE 4 COMPLETE")
    print("Report:", OUTPUT_FILE)

    print("\nTop 15 Overall Pairs:")
    print(pair_freq.head(15).to_string(index=False))

    print("\nTop 15 Recent 100 Pairs:")
    print(recent_100.head(15).to_string(index=False))


if __name__ == "__main__":
    main()