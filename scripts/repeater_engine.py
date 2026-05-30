import sys
import sqlite3
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent.parent))

from config import DATABASE_FILE, REPORTS_DIR

OUTPUT_FILE = REPORTS_DIR / "PHASE_17_REPEATER_ENGINE.xlsx"

WINDOWS = [7, 15, 30, 60, 100]


def load_draws():
    conn = sqlite3.connect(DATABASE_FILE)

    df = pd.read_sql_query("""
        SELECT draw_date, draw_type, number, box
        FROM draws
        ORDER BY draw_date, draw_type
    """, conn)

    conn.close()

    df["draw_date"] = pd.to_datetime(df["draw_date"])
    df["number"] = df["number"].astype(str).str.zfill(3)

    df = df.sort_values(["draw_date", "draw_type"]).reset_index(drop=True)
    df["draw_index"] = df.index + 1

    return df


def all_numbers():
    return [str(i).zfill(3) for i in range(1000)]


def build_repeater_report(df):
    rows = []

    for number in all_numbers():
        hits = df[df["number"] == number].copy()

        indexes = hits["draw_index"].tolist()
        total_hits = len(indexes)

        repeat_gaps = []

        for i in range(1, len(indexes)):
            repeat_gaps.append(indexes[i] - indexes[i - 1])

        row = {
            "Number": number,
            "Total Hits": total_hits,
            "Repeat Count": max(total_hits - 1, 0),
        }

        for window in WINDOWS:
            row[f"Repeats Within {window} Draws"] = sum(
                1 for gap in repeat_gaps if gap <= window
            )

            row[f"Repeat Rate {window}"] = (
                round(
                    row[f"Repeats Within {window} Draws"] / len(repeat_gaps),
                    4
                )
                if repeat_gaps else 0
            )

        row["Average Repeat Gap"] = (
            round(sum(repeat_gaps) / len(repeat_gaps), 2)
            if repeat_gaps else None
        )

        row["Min Repeat Gap"] = min(repeat_gaps) if repeat_gaps else None
        row["Max Repeat Gap"] = max(repeat_gaps) if repeat_gaps else None

        rows.append(row)

    return pd.DataFrame(rows)


def build_recent_repeaters(df, lookback=100):
    recent = df.tail(lookback)

    counts = (
        recent.groupby("number")
        .size()
        .reset_index(name=f"Hits Last {lookback}")
        .sort_values(f"Hits Last {lookback}", ascending=False)
    )

    return counts


def main():
    print("Loading data...")
    df = load_draws()

    print("Building repeater report...")
    repeater = build_repeater_report(df)

    print("Building recent repeaters...")
    recent_100 = build_recent_repeaters(df, 100)
    recent_200 = build_recent_repeaters(df, 200)

    strongest_repeaters = repeater[
        repeater["Total Hits"] >= 3
    ].sort_values(
        ["Repeat Rate 100", "Total Hits"],
        ascending=[False, False]
    )

    fastest_repeaters = repeater[
        repeater["Total Hits"] >= 3
    ].sort_values(
        ["Min Repeat Gap", "Total Hits"],
        ascending=[True, False]
    )

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
        repeater.to_excel(writer, sheet_name="All Repeaters", index=False)
        strongest_repeaters.to_excel(writer, sheet_name="Strongest Repeaters", index=False)
        fastest_repeaters.to_excel(writer, sheet_name="Fastest Repeaters", index=False)
        recent_100.to_excel(writer, sheet_name="Recent 100 Repeaters", index=False)
        recent_200.to_excel(writer, sheet_name="Recent 200 Repeaters", index=False)

    print("\nPHASE 17 COMPLETE")
    print("Report:", OUTPUT_FILE)

    print("\nSTRONGEST REPEATERS")
    print(
        strongest_repeaters.head(20)[
            [
                "Number",
                "Total Hits",
                "Repeat Count",
                "Repeat Rate 30",
                "Repeat Rate 60",
                "Repeat Rate 100",
                "Average Repeat Gap",
            ]
        ].to_string(index=False)
    )

    print("\nRECENT 100 REPEATERS")
    print(recent_100.head(20).to_string(index=False))


if __name__ == "__main__":
    main()