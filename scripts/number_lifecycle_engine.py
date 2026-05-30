import sys
import sqlite3
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent.parent))

from config import DATABASE_FILE, REPORTS_DIR

OUTPUT_FILE = REPORTS_DIR / "PHASE_16_NUMBER_LIFECYCLE.xlsx"


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
    df["year"] = df["draw_date"].dt.year

    df = df.sort_values(["draw_date", "draw_type"]).reset_index(drop=True)
    df["draw_index"] = df.index + 1

    return df


def all_numbers():
    return [str(i).zfill(3) for i in range(1000)]


def build_lifecycle(df):
    latest_index = df["draw_index"].max()
    years = sorted(df["year"].unique())

    rows = []

    for number in all_numbers():
        hits = df[df["number"] == number].copy()

        total_hits = len(hits)

        year_counts = {
            f"{year} Hits": int((hits["year"] == year).sum())
            for year in years
        }

        if total_hits > 0:
            indexes = hits["draw_index"].tolist()

            gaps = [
                indexes[i] - indexes[i - 1]
                for i in range(1, len(indexes))
            ]

            first_seen = hits["draw_date"].min().date()
            last_seen = hits["draw_date"].max().date()
            last_seen_draw = hits.sort_values("draw_index").iloc[-1]["draw_type"]

            current_skip = latest_index - max(indexes)

            avg_gap = round(sum(gaps) / len(gaps), 2) if gaps else None
            min_gap = min(gaps) if gaps else None
            max_gap = max(gaps) if gaps else None

            repeated = total_hits - 1

        else:
            first_seen = None
            last_seen = None
            last_seen_draw = None
            current_skip = latest_index
            avg_gap = None
            min_gap = None
            max_gap = None
            repeated = 0

        rows.append({
            "Number": number,
            "Total Hits": total_hits,
            **year_counts,
            "First Seen": first_seen,
            "Last Seen": last_seen,
            "Last Seen Draw": last_seen_draw,
            "Current Skip": current_skip,
            "Average Gap": avg_gap,
            "Min Gap": min_gap,
            "Max Gap": max_gap,
            "Repeat Count": repeated,
        })

    return pd.DataFrame(rows)


def main():
    print("Loading data...")
    df = load_draws()

    print("Building number lifecycle...")
    lifecycle = build_lifecycle(df)

    most_frequent = lifecycle.sort_values(
        ["Total Hits", "Current Skip"],
        ascending=[False, False]
    )

    most_overdue = lifecycle[
        lifecycle["Total Hits"] >= 2
    ].sort_values(
        "Current Skip",
        ascending=False
    )

    never_seen = lifecycle[
        lifecycle["Total Hits"] == 0
    ].sort_values("Number")

    seen_this_year = lifecycle[
        lifecycle.get(f"{df['year'].max()} Hits", 0) > 0
    ].sort_values(
        f"{df['year'].max()} Hits",
        ascending=False
    )

    not_seen_this_year = lifecycle[
        lifecycle.get(f"{df['year'].max()} Hits", 0) == 0
    ].sort_values(
        ["Total Hits", "Current Skip"],
        ascending=[False, False]
    )

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
        lifecycle.to_excel(writer, sheet_name="All Numbers", index=False)
        most_frequent.to_excel(writer, sheet_name="Most Frequent", index=False)
        most_overdue.to_excel(writer, sheet_name="Most Overdue", index=False)
        never_seen.to_excel(writer, sheet_name="Never Seen", index=False)
        seen_this_year.to_excel(writer, sheet_name="Seen This Year", index=False)
        not_seen_this_year.to_excel(writer, sheet_name="Not Seen This Year", index=False)

    print("\nPHASE 16 COMPLETE")
    print("Report:", OUTPUT_FILE)

    print("\nMOST FREQUENT NUMBERS")
    print(
        most_frequent.head(20)[
            [
                "Number",
                "Total Hits",
                "Current Skip",
                "Average Gap",
                "Last Seen",
                "Last Seen Draw",
            ]
        ].to_string(index=False)
    )

    print("\nMOST OVERDUE NUMBERS WITH 2+ HITS")
    print(
        most_overdue.head(20)[
            [
                "Number",
                "Total Hits",
                "Current Skip",
                "Average Gap",
                "Last Seen",
                "Last Seen Draw",
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()