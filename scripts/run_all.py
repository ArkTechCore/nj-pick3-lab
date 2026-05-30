import subprocess
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
LOG_FILE = ROOT / "logs" / "pipeline.log"

SCRIPTS = [
    "collect_draws.py",
    "validate_data.py",
    "stats_engine.py",
    "pair_engine.py",
    "sum_engine.py",
    "pattern_engine.py",
    "rolling_engine.py",
    "skip_tracker.py",
    "midday_model.py",
    "evening_model.py",
    "master_scoring_engine.py",
    "candidate_generator.py",
    "straight_order_engine.py",
    "precision_pick_engine.py",
    "final_report_generator.py",
    "groq_ai_analyst.py",
    "archive_snapshot.py",
    "number_lifecycle_engine.py",
    "repeater_engine.py",
    "consensus_pick_engine.py",
]


def write_log(message):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")


def run_script(script_name):
    script_path = ROOT / "scripts" / script_name

    print("\n" + "=" * 70)
    print(f"RUNNING: {script_name}")
    print("=" * 70)

    write_log(f"START {script_name}")

    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=ROOT
    )

    if result.returncode != 0:
        write_log(f"FAILED {script_name}")
        print(f"\nFAILED: {script_name}")
        sys.exit(result.returncode)

    write_log(f"SUCCESS {script_name}")
    print(f"\nSUCCESS: {script_name}")


def main():
    start = datetime.now()

    write_log("PIPELINE START")

    print("\nNJ PICK 3 LAB")
    print("Pipeline Started:", start.strftime("%Y-%m-%d %H:%M:%S"))

    for script in SCRIPTS:
        run_script(script)

    end = datetime.now()

    write_log("PIPELINE COMPLETE")

    print("\n" + "=" * 70)
    print("PIPELINE COMPLETE")
    print("=" * 70)

    print("Started :", start.strftime("%Y-%m-%d %H:%M:%S"))
    print("Finished:", end.strftime("%Y-%m-%d %H:%M:%S"))
    print("Duration:", end - start)

    print("\nGenerated Reports:")

    reports_dir = ROOT / "data" / "reports"

    if reports_dir.exists():
        for file in sorted(reports_dir.glob("*")):
            print("-", file.name)


if __name__ == "__main__":
    main()