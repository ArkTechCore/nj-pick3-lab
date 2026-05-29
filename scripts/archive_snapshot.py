import shutil
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent

REPORTS_DIR = ROOT / "data" / "reports"
SNAPSHOTS_DIR = ROOT / "data" / "snapshots"
LOG_FILE = ROOT / "logs" / "pipeline.log"

FILES_TO_SNAPSHOT = [
    "MASTER_FINAL_REPORT.xlsx",
    "PHASE_13_GROQ_AI_ANALYSIS.txt",
]


def write_log(message):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")


def main():
    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")

    print("\nCreating snapshots...")

    for filename in FILES_TO_SNAPSHOT:
        source = REPORTS_DIR / filename

        if not source.exists():
            print(f"Missing, skipped: {filename}")
            write_log(f"SNAPSHOT SKIPPED missing {filename}")
            continue

        snapshot_name = f"{source.stem}_{timestamp}{source.suffix}"
        destination = SNAPSHOTS_DIR / snapshot_name

        shutil.copy2(source, destination)

        print(f"Snapshot saved: {destination}")
        write_log(f"SNAPSHOT SAVED {destination.name}")

    print("\nSnapshots complete.")


if __name__ == "__main__":
    main()