import sys
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent.parent))

from config import REPORTS_DIR

OUTPUT_FILE = REPORTS_DIR / "PHASE_18_CONSENSUS_PICK_ENGINE.xlsx"


def read_excel(file_name, sheet_name):
    path = REPORTS_DIR / file_name

    if not path.exists():
        print(f"Missing file: {path}")
        return pd.DataFrame()

    try:
        return pd.read_excel(path, sheet_name=sheet_name)
    except Exception as e:
        print(f"Could not read {file_name} / {sheet_name}: {e}")
        return pd.DataFrame()


def normalize(series):
    max_val = series.max()

    if max_val == 0:
        return series * 0

    return series / max_val


def main():
    print("Loading engine outputs...")

    master = read_excel(
        "PHASE_11_MASTER_SCORING.xlsx",
        "All Box Rankings"
    )

    candidates = read_excel(
        "PHASE_11_5_CANDIDATES.xlsx",
        "All Candidates"
    )

    precision = read_excel(
        "PHASE_15_PRECISION_PICK_ENGINE.xlsx",
        "All Precision Scores"
    )

    lifecycle = read_excel(
        "PHASE_16_NUMBER_LIFECYCLE.xlsx",
        "All Numbers"
    )

    repeaters = read_excel(
        "PHASE_17_REPEATER_ENGINE.xlsx",
        "All Repeaters"
    )

    if master.empty or candidates.empty or precision.empty:
        raise RuntimeError(
            "Missing required reports. Run run_all.py first."
        )

    # ==========================
    # PREP MASTER BOX SCORE
    # ==========================
    master["Box"] = master["Box"].astype(str).str.zfill(3)
    master_small = master[["Box", "Master Score"]].copy()

    # ==========================
    # PREP CANDIDATE BOX SCORE
    # ==========================
    candidates["Box"] = candidates["Box"].astype(str).str.zfill(3)
    candidates_small = candidates[["Box", "Candidate Score"]].copy()

    # ==========================
    # PREP PRECISION STRAIGHT SCORE
    # ==========================
    precision["Box"] = precision["Box"].astype(str).str.zfill(3)
    precision["Straight"] = precision["Straight"].astype(str).str.zfill(3)

    precision_small = precision[
        [
            "Box",
            "Straight",
            "Precision Score",
            "Evening Position Score",
            "Midday Position Score",
            "Sum",
        ]
    ].copy()

    # ==========================
    # PREP LIFECYCLE
    # ==========================
    if not lifecycle.empty:
        lifecycle["Number"] = lifecycle["Number"].astype(str).str.zfill(3)

        lifecycle_small = lifecycle[
            [
                "Number",
                "Total Hits",
                "Current Skip",
                "Average Gap",
                "Repeat Count",
            ]
        ].copy()

        lifecycle_small = lifecycle_small.rename(
            columns={"Number": "Straight"}
        )
    else:
        lifecycle_small = pd.DataFrame()

    # ==========================
    # PREP REPEATERS
    # ==========================
    if not repeaters.empty:
        repeaters["Number"] = repeaters["Number"].astype(str).str.zfill(3)

        repeater_cols = [
            "Number",
            "Repeat Rate 30",
            "Repeat Rate 60",
            "Repeat Rate 100",
            "Average Repeat Gap",
        ]

        available_cols = [
            c for c in repeater_cols
            if c in repeaters.columns
        ]

        repeaters_small = repeaters[available_cols].copy()
        repeaters_small = repeaters_small.rename(
            columns={"Number": "Straight"}
        )
    else:
        repeaters_small = pd.DataFrame()

    # ==========================
    # MERGE EVERYTHING
    # ==========================
    df = precision_small.merge(
        master_small,
        on="Box",
        how="left"
    )

    df = df.merge(
        candidates_small,
        on="Box",
        how="left"
    )

    if not lifecycle_small.empty:
        df = df.merge(
            lifecycle_small,
            on="Straight",
            how="left"
        )

    if not repeaters_small.empty:
        df = df.merge(
            repeaters_small,
            on="Straight",
            how="left"
        )

    df = df.fillna(0)

    # ==========================
    # NORMALIZED SCORES
    # ==========================
    df["Master Norm"] = normalize(df["Master Score"])
    df["Candidate Norm"] = normalize(df["Candidate Score"])
    df["Precision Norm"] = normalize(df["Precision Score"])
    df["Evening Position Norm"] = normalize(df["Evening Position Score"])
    df["Midday Position Norm"] = normalize(df["Midday Position Score"])
    df["Total Hits Norm"] = normalize(df["Total Hits"])
    df["Current Skip Norm"] = normalize(df["Current Skip"])
    df["Repeat Rate 100 Norm"] = normalize(df.get("Repeat Rate 100", pd.Series([0] * len(df))))

    # ==========================
    # CONSENSUS SCORE
    # ==========================
    df["Consensus Score"] = (
        df["Precision Norm"] * 0.30
        + df["Master Norm"] * 0.20
        + df["Candidate Norm"] * 0.15
        + df["Evening Position Norm"] * 0.12
        + df["Midday Position Norm"] * 0.08
        + df["Total Hits Norm"] * 0.06
        + df["Current Skip Norm"] * 0.05
        + df["Repeat Rate 100 Norm"] * 0.04
    )

    df = df.sort_values(
        "Consensus Score",
        ascending=False
    )

    # Top straight picks overall
    top_10_straight = df.head(10).copy()

    # Diversified version: one straight per box
    top_by_box = (
        df.sort_values("Consensus Score", ascending=False)
        .groupby("Box")
        .head(1)
        .reset_index(drop=True)
    )

    diversified_top_10 = top_by_box.head(10).copy()

    evening_top_10 = df.sort_values(
        ["Evening Position Norm", "Consensus Score"],
        ascending=False
    ).head(10).copy()

    midday_top_10 = df.sort_values(
        ["Midday Position Norm", "Consensus Score"],
        ascending=False
    ).head(10).copy()

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="All Consensus Scores", index=False)
        top_10_straight.to_excel(writer, sheet_name="Top 10 Straight", index=False)
        diversified_top_10.to_excel(writer, sheet_name="Diversified Top 10", index=False)
        evening_top_10.to_excel(writer, sheet_name="Evening Top 10", index=False)
        midday_top_10.to_excel(writer, sheet_name="Midday Top 10", index=False)

    print("\nPHASE 18 COMPLETE")
    print("Report:", OUTPUT_FILE)

    print("\nFINAL CONSENSUS TOP 10 STRAIGHT")
    print(
        top_10_straight[
            [
                "Straight",
                "Box",
                "Consensus Score",
                "Precision Score",
                "Master Score",
                "Candidate Score",
                "Current Skip",
                "Repeat Rate 100",
            ]
        ].to_string(index=False)
    )

    print("\nDIVERSIFIED TOP 10")
    print(
        diversified_top_10[
            [
                "Straight",
                "Box",
                "Consensus Score",
                "Precision Score",
                "Master Score",
                "Candidate Score",
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()