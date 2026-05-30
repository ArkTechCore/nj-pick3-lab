import sys
import sqlite3
import itertools
from pathlib import Path
from collections import Counter

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent.parent))

from config import DATABASE_FILE, REPORTS_DIR

OUTPUT_FILE = REPORTS_DIR / "PHASE_14_STRAIGHT_ORDER_ENGINE.xlsx"


def load_draws():
    conn = sqlite3.connect(DATABASE_FILE)

    df = pd.read_sql_query(
        """
        SELECT draw_date, draw_type, number, box
        FROM draws
        ORDER BY draw_date, draw_type
        """,
        conn,
    )

    conn.close()

    df["number"] = df["number"].astype(str).str.zfill(3)

    return df


def build_position_stats(df):
    pos1 = Counter()
    pos2 = Counter()
    pos3 = Counter()

    recent100 = df.tail(100)

    for num in recent100["number"]:
        pos1[num[0]] += 1
        pos2[num[1]] += 1
        pos3[num[2]] += 1

    return pos1, pos2, pos3


def score_straight(number, pos1, pos2, pos3):
    return (
        pos1[number[0]]
        + pos2[number[1]]
        + pos3[number[2]]
    )


def main():

    master_file = REPORTS_DIR / "MASTER_FINAL_REPORT.xlsx"

    if not master_file.exists():
        raise FileNotFoundError(
            "MASTER_FINAL_REPORT.xlsx not found. Run Phase 12 first."
        )

    draws = load_draws()

    pos1, pos2, pos3 = build_position_stats(draws)

    master = pd.read_excel(
        master_file,
        sheet_name="Top_25_Master"
    )

    rows = []

    for _, row in master.head(25).iterrows():

        box = str(row["Box"]).zfill(3)

        perms = sorted(
            set(
                "".join(p)
                for p in itertools.permutations(box)
            )
        )

        for straight in perms:

            score = score_straight(
                straight,
                pos1,
                pos2,
                pos3
            )

            rows.append({
                "Box": box,
                "Straight": straight,
                "Position Score": score
            })

    result = pd.DataFrame(rows)

    result = result.sort_values(
        "Position Score",
        ascending=False
    )

    best_per_box = (
        result
        .sort_values("Position Score", ascending=False)
        .groupby("Box")
        .head(1)
        .reset_index(drop=True)
    )

    REPORTS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    with pd.ExcelWriter(
        OUTPUT_FILE,
        engine="openpyxl"
    ) as writer:

        result.to_excel(
            writer,
            sheet_name="All Straight Scores",
            index=False
        )

        best_per_box.to_excel(
            writer,
            sheet_name="Best Straight Per Box",
            index=False
        )

    print("\nPHASE 14 COMPLETE")
    print("Report:", OUTPUT_FILE)

    print("\nTOP STRAIGHT PICKS\n")
    print(
        best_per_box.head(20).to_string(index=False)
    )


if __name__ == "__main__":
    main()