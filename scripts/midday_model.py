import sys
import sqlite3
import itertools
from pathlib import Path
from collections import Counter

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent.parent))

from config import DATABASE_FILE, REPORTS_DIR

OUTPUT_FILE = REPORTS_DIR / "PHASE_9_MIDDAY_MODEL.xlsx"


def load_data():
    conn = sqlite3.connect(DATABASE_FILE)

    df = pd.read_sql_query("""
        SELECT draw_date, draw_type, number, box
        FROM draws
        WHERE draw_type='Midday'
    """, conn)

    conn.close()

    df["draw_date"] = pd.to_datetime(df["draw_date"])
    df["number"] = df["number"].astype(str).str.zfill(3)

    return df.sort_values("draw_date")


def digit_sum(n):
    return sum(int(x) for x in str(n))


def get_pairs(n):
    return [
        "".join(sorted(p))
        for p in itertools.combinations(str(n), 2)
    ]


def main():

    df = load_data()

    digits = Counter("".join(df["number"]))
    pairs = Counter()
    sums = Counter(df["number"].apply(digit_sum))
    boxes = Counter(df["box"])

    for n in df["number"]:
        pairs.update(get_pairs(n))

    digit_df = (
        pd.DataFrame(digits.items(), columns=["Digit", "Hits"])
        .sort_values("Hits", ascending=False)
    )

    pair_df = (
        pd.DataFrame(pairs.items(), columns=["Pair", "Hits"])
        .sort_values("Hits", ascending=False)
    )

    sum_df = (
        pd.DataFrame(sums.items(), columns=["Sum", "Hits"])
        .sort_values("Hits", ascending=False)
    )

    box_df = (
        pd.DataFrame(boxes.items(), columns=["Box", "Hits"])
        .sort_values("Hits", ascending=False)
    )

    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
        digit_df.to_excel(writer, sheet_name="Hot Digits", index=False)
        pair_df.to_excel(writer, sheet_name="Hot Pairs", index=False)
        sum_df.to_excel(writer, sheet_name="Hot Sums", index=False)
        box_df.to_excel(writer, sheet_name="Hot Boxes", index=False)

    print("\nPHASE 9 COMPLETE")
    print("Midday Draws:", len(df))
    print("Report:", OUTPUT_FILE)

    print("\nTop 10 Midday Digits")
    print(digit_df.head(10).to_string(index=False))

    print("\nTop 10 Midday Pairs")
    print(pair_df.head(10).to_string(index=False))

    print("\nTop 10 Midday Sums")
    print(sum_df.head(10).to_string(index=False))


if __name__ == "__main__":
    main()