import sys
import sqlite3
import itertools
from pathlib import Path
from collections import Counter

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent.parent))

from config import DATABASE_FILE, REPORTS_DIR

OUTPUT_FILE = REPORTS_DIR / "PHASE_15_PRECISION_PICK_ENGINE.xlsx"


def box_number(n):
    return "".join(sorted(str(n).zfill(3)))


def digit_sum(n):
    return sum(int(x) for x in str(n).zfill(3))


def get_pairs(n):
    return ["".join(sorted(p)) for p in itertools.combinations(str(n).zfill(3), 2)]


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
    df["box"] = df["box"].astype(str).str.zfill(3)

    return df


def position_counter(df):
    p1, p2, p3 = Counter(), Counter(), Counter()

    for n in df["number"]:
        p1[n[0]] += 1
        p2[n[1]] += 1
        p3[n[2]] += 1

    return p1, p2, p3


def score_position(n, p1, p2, p3):
    return p1[n[0]] + p2[n[1]] + p3[n[2]]


def normalize(value, max_value):
    if max_value == 0:
        return 0
    return value / max_value


def main():
    draws = load_draws()

    recent_30 = draws.tail(30)
    recent_60 = draws.tail(60)
    recent_100 = draws.tail(100)

    evening = draws[draws["draw_type"] == "Evening"]
    midday = draws[draws["draw_type"] == "Midday"]

    p_all_100 = position_counter(recent_100)
    p_evening = position_counter(evening.tail(100))
    p_midday = position_counter(midday.tail(100))

    box_hits_all = Counter(draws["box"])
    box_hits_30 = Counter(recent_30["box"])
    box_hits_60 = Counter(recent_60["box"])
    box_hits_100 = Counter(recent_100["box"])

    digit_recent = Counter("".join(recent_100["number"]))

    pair_recent = Counter()
    for n in recent_100["number"]:
        pair_recent.update(get_pairs(n))

    sum_recent = Counter(recent_100["number"].apply(digit_sum))

    all_boxes = sorted(set(box_number(i) for i in range(1000)))

    rows = []

    max_box_all = max(box_hits_all.values()) if box_hits_all else 1
    max_box_30 = max(box_hits_30.values()) if box_hits_30 else 1
    max_box_60 = max(box_hits_60.values()) if box_hits_60 else 1
    max_box_100 = max(box_hits_100.values()) if box_hits_100 else 1

    max_digit = max(digit_recent.values()) if digit_recent else 1
    max_pair = max(pair_recent.values()) if pair_recent else 1
    max_sum = max(sum_recent.values()) if sum_recent else 1

    for box in all_boxes:
        perms = sorted(set("".join(p) for p in itertools.permutations(box)))

        box_all_score = normalize(box_hits_all.get(box, 0), max_box_all)
        box_30_score = normalize(box_hits_30.get(box, 0), max_box_30)
        box_60_score = normalize(box_hits_60.get(box, 0), max_box_60)
        box_100_score = normalize(box_hits_100.get(box, 0), max_box_100)

        digit_score = sum(digit_recent.get(d, 0) for d in box) / (max_digit * 3)

        pair_score = sum(pair_recent.get(p, 0) for p in get_pairs(box)) / (max_pair * 3)

        sum_score = normalize(sum_recent.get(digit_sum(box), 0), max_sum)

        box_base_score = (
            box_all_score * 0.20
            + box_30_score * 0.20
            + box_60_score * 0.15
            + box_100_score * 0.15
            + digit_score * 0.12
            + pair_score * 0.13
            + sum_score * 0.05
        )

        for straight in perms:
            all_position_score = score_position(straight, *p_all_100)
            evening_position_score = score_position(straight, *p_evening)
            midday_position_score = score_position(straight, *p_midday)

            precision_score = (
                box_base_score * 0.65
                + normalize(all_position_score, 100) * 0.15
                + normalize(evening_position_score, 100) * 0.12
                + normalize(midday_position_score, 100) * 0.08
            )

            rows.append({
                "Box": box,
                "Straight": straight,
                "Box Base Score": round(box_base_score, 5),
                "All Position Score": all_position_score,
                "Evening Position Score": evening_position_score,
                "Midday Position Score": midday_position_score,
                "Precision Score": round(precision_score, 5),
                "Sum": digit_sum(straight),
            })

    result = pd.DataFrame(rows).sort_values(
        "Precision Score",
        ascending=False
    )

    top_10_straight = result.head(10).copy()

    best_by_box = (
        result
        .sort_values("Precision Score", ascending=False)
        .groupby("Box")
        .head(1)
        .reset_index(drop=True)
        .head(25)
    )

    top_evening = result.sort_values(
        ["Evening Position Score", "Precision Score"],
        ascending=False
    ).head(25)

    top_midday = result.sort_values(
        ["Midday Position Score", "Precision Score"],
        ascending=False
    ).head(25)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
        result.to_excel(writer, sheet_name="All Precision Scores", index=False)
        top_10_straight.to_excel(writer, sheet_name="Top 10 Straight", index=False)
        best_by_box.to_excel(writer, sheet_name="Best By Box", index=False)
        top_evening.to_excel(writer, sheet_name="Evening Precision", index=False)
        top_midday.to_excel(writer, sheet_name="Midday Precision", index=False)

    print("\nPHASE 15 COMPLETE")
    print("Report:", OUTPUT_FILE)

    print("\nTOP 10 PRECISION STRAIGHT PICKS")
    print(
        top_10_straight[
            [
                "Straight",
                "Box",
                "Precision Score",
                "Box Base Score",
                "All Position Score",
                "Evening Position Score",
                "Midday Position Score",
                "Sum",
            ]
        ].to_string(index=False)
    )

    print("\nBEST STRAIGHT ORDER BY BOX")
    print(
        best_by_box.head(15)[
            [
                "Box",
                "Straight",
                "Precision Score",
                "Evening Position Score",
                "Midday Position Score",
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()