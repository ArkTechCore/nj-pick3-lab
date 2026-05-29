import sys
import sqlite3
import itertools
from pathlib import Path
from collections import Counter

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent.parent))

from config import DATABASE_FILE, REPORTS_DIR
from scripts.load_settings import TOP_CANDIDATE_COUNT

OUTPUT_FILE = REPORTS_DIR / "PHASE_11_5_CANDIDATES.xlsx"


def box_number(n):
    return "".join(sorted(str(n).zfill(3)))


def digit_sum(n):
    return sum(int(x) for x in str(n).zfill(3))


def get_pairs(n):
    return ["".join(sorted(p)) for p in itertools.combinations(str(n).zfill(3), 2)]


def load_data():
    conn = sqlite3.connect(DATABASE_FILE)

    df = pd.read_sql_query(
        "SELECT draw_date, draw_type, number, box FROM draws",
        conn
    )

    conn.close()

    df["draw_date"] = pd.to_datetime(df["draw_date"])
    df["number"] = df["number"].astype(str).str.zfill(3)

    return df.sort_values(["draw_date", "draw_type"])


def straight_plays(box):
    return ", ".join(
        sorted(
            set(
                "".join(p)
                for p in itertools.permutations(box)
            )
        )
    )


def main():
    df = load_data()

    recent100 = df.tail(100)

    hot_digits = Counter("".join(recent100["number"]))
    hot_boxes = Counter(recent100["box"])

    pair_counter = Counter()

    for n in recent100["number"]:
        pair_counter.update(get_pairs(n))

    sum_counter = Counter(recent100["number"].apply(digit_sum))

    rows = []

    for box in sorted(set(df["box"])):
        digit_score = sum(hot_digits.get(d, 0) for d in box)
        pair_score = sum(pair_counter.get(p, 0) for p in get_pairs(box))
        sum_score = sum_counter.get(digit_sum(box), 0)
        recent_hits = hot_boxes.get(box, 0)

        score = (
            digit_score * 0.40
            + pair_score * 0.35
            + sum_score * 0.20
            + recent_hits * 0.05
        )

        rows.append({
            "Box": box,
            "Digit Score": digit_score,
            "Pair Score": pair_score,
            "Sum Score": sum_score,
            "Recent Hits": recent_hits,
            "Candidate Score": round(score, 2)
        })

    result = pd.DataFrame(rows).sort_values(
        "Candidate Score",
        ascending=False
    )

    top_candidates = result.head(TOP_CANDIDATE_COUNT).copy()

    top_candidates["Straight Plays"] = top_candidates["Box"].apply(straight_plays)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    top_sheet_name = f"Top {TOP_CANDIDATE_COUNT} Candidates"[:31]

    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
        result.to_excel(
            writer,
            sheet_name="All Candidates",
            index=False
        )

        top_candidates.to_excel(
            writer,
            sheet_name=top_sheet_name,
            index=False
        )

    print("\nPHASE 11.5 COMPLETE")
    print("Report:", OUTPUT_FILE)
    print("Top Candidate Count:", TOP_CANDIDATE_COUNT)

    print(f"\nTOP {TOP_CANDIDATE_COUNT} CANDIDATES\n")
    print(
        top_candidates[
            [
                "Box",
                "Candidate Score",
                "Digit Score",
                "Pair Score",
                "Sum Score"
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()