import sys, sqlite3, itertools
from pathlib import Path
from collections import Counter
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import DATABASE_FILE, REPORTS_DIR

OUTPUT_FILE = REPORTS_DIR / "PHASE_11_MASTER_SCORING.xlsx"

def box_number(n):
    return "".join(sorted(str(n).zfill(3)))

def digit_sum(n):
    return sum(int(x) for x in str(n).zfill(3))

def number_type(n):
    s = str(n).zfill(3)
    if len(set(s)) == 1:
        return "Triple"
    if len(set(s)) == 2:
        return "Double"
    return "Single"

def get_pairs(n):
    return ["".join(sorted(p)) for p in itertools.combinations(str(n).zfill(3), 2)]

def all_boxes():
    return sorted(set(box_number(i) for i in range(1000)))

def norm(series):
    max_val = series.max()
    if max_val == 0:
        return series * 0
    return series / max_val

def load_data():
    conn = sqlite3.connect(DATABASE_FILE)
    df = pd.read_sql_query("SELECT draw_date, draw_type, number, box FROM draws", conn)
    conn.close()
    df["draw_date"] = pd.to_datetime(df["draw_date"])
    df["number"] = df["number"].astype(str).str.zfill(3)
    df = df.sort_values(["draw_date", "draw_type"]).reset_index(drop=True)
    df["draw_index"] = df.index + 1
    return df

def main():
    df = load_data()
    latest_index = df["draw_index"].max()

    digit_counts = Counter("".join(df["number"].tolist()))
    pair_counts = Counter()
    sum_counts = Counter(df["number"].apply(digit_sum))
    box_counts = Counter(df["box"])

    recent = df.tail(100)
    recent_box_counts = Counter(recent["box"])
    recent_digit_counts = Counter("".join(recent["number"].tolist()))

    for n in df["number"]:
        pair_counts.update(get_pairs(n))

    rows = []

    for box in all_boxes():
        hits = box_counts.get(box, 0)

        seen = df[df["box"] == box]
        if len(seen) > 0:
            last_seen = seen["draw_index"].max()
            last_seen_date = seen["draw_date"].max().date()
        else:
            last_seen = 0
            last_seen_date = ""

        skip = latest_index - last_seen

        digit_strength = sum(digit_counts.get(d, 0) for d in box)
        recent_digit_strength = sum(recent_digit_counts.get(d, 0) for d in box)
        pair_strength = sum(pair_counts.get(p, 0) for p in get_pairs(box))
        sum_strength = sum_counts.get(digit_sum(box), 0)
        recent_hits = recent_box_counts.get(box, 0)

        t = number_type(box)

        if t == "Single":
            type_bonus = 1.00
        elif t == "Double":
            type_bonus = 0.60
        else:
            type_bonus = 0.15

        rows.append({
            "Box": box,
            "Type": t,
            "Sum": digit_sum(box),
            "Hits": hits,
            "Recent 100 Hits": recent_hits,
            "Current Skip": skip,
            "Digit Strength": digit_strength,
            "Recent Digit Strength": recent_digit_strength,
            "Pair Strength": pair_strength,
            "Sum Strength": sum_strength,
            "Type Bonus": type_bonus,
            "Last Seen Date": last_seen_date,
        })

    score = pd.DataFrame(rows)

    score["Hits Score"] = norm(score["Hits"])
    score["Recent Box Score"] = norm(score["Recent 100 Hits"])
    score["Skip Score"] = norm(score["Current Skip"])
    score["Digit Score"] = norm(score["Digit Strength"])
    score["Recent Digit Score"] = norm(score["Recent Digit Strength"])
    score["Pair Score"] = norm(score["Pair Strength"])
    score["Sum Score"] = norm(score["Sum Strength"])

    score["Master Score"] = (
        score["Hits Score"] * 0.20
        + score["Recent Box Score"] * 0.18
        + score["Skip Score"] * 0.15
        + score["Digit Score"] * 0.14
        + score["Recent Digit Score"] * 0.10
        + score["Pair Score"] * 0.15
        + score["Sum Score"] * 0.05
        + score["Type Bonus"] * 0.03
    )

    score = score.sort_values("Master Score", ascending=False)

    top_plays = score.head(100).copy()
    top_plays["Straight Variations"] = top_plays["Box"].apply(
        lambda x: ", ".join(sorted(set("".join(p) for p in itertools.permutations(x))))
    )

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
        score.to_excel(writer, sheet_name="All Box Rankings", index=False)
        top_plays.to_excel(writer, sheet_name="Top 100 Plays", index=False)

    print("\nPHASE 11 COMPLETE")
    print("Report:", OUTPUT_FILE)

    print("\nTop 25 Master Box Picks:")
    print(top_plays[[
        "Box", "Type", "Sum", "Hits", "Recent 100 Hits",
        "Current Skip", "Master Score", "Straight Variations"
    ]].head(25).to_string(index=False))

    print("\nReminder: this ranks historical patterns only. Lottery is random.")

if __name__ == "__main__":
    main()