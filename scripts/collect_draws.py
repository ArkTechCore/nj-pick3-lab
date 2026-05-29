import re
import sys
import sqlite3
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent.parent))

from config import DATABASE_FILE

from scripts.load_settings import START_YEAR, END_YEAR

YEARS = list(range(START_YEAR, END_YEAR + 1))

SOURCES = {
    "Midday": "https://www.lottery.net/new-jersey/pick-3-midday/results/{}",
    "Evening": "https://www.lottery.net/new-jersey/pick-3-evening/results/{}",
}


def box_number(n):
    return "".join(sorted(str(n).zfill(3)))


def parse_page(url, year, draw_type):
    df = pd.read_html(url)[0]
    rows = []

    for _, row in df.iterrows():
        draw_date = pd.to_datetime(row["Result Date"], errors="coerce")

        if pd.isna(draw_date):
            continue

        if draw_date.year != year:
            continue

        digits = re.findall(r"\d", str(row["Results"]))

        if len(digits) < 3:
            continue

        number = "".join(digits[:3])
        fireball = digits[3] if len(digits) > 3 else ""

        rows.append({
            "draw_date": draw_date.date().isoformat(),
            "draw_type": draw_type,
            "number": number,
            "box": box_number(number),
            "fireball": fireball,
            "source": url,
        })

    return rows


def insert_rows(rows):
    conn = sqlite3.connect(DATABASE_FILE)
    cur = conn.cursor()

    inserted = 0
    skipped = 0

    for r in rows:
        cur.execute(
            "SELECT id FROM draws WHERE draw_date=? AND draw_type=?",
            (r["draw_date"], r["draw_type"])
        )

        if cur.fetchone():
            skipped += 1
            continue

        cur.execute("""
            INSERT INTO draws (draw_date, draw_type, number, box, source)
            VALUES (?, ?, ?, ?, ?)
        """, (
            r["draw_date"],
            r["draw_type"],
            r["number"],
            r["box"],
            r["source"],
        ))

        inserted += 1

    conn.commit()
    conn.close()

    return inserted, skipped


def main():
    total = 0

    for year in YEARS:
        for draw_type, template in SOURCES.items():
            url = template.format(year)

            print(f"Collecting {year} {draw_type}...")
            rows = parse_page(url, year, draw_type)
            inserted, skipped = insert_rows(rows)

            print("Parsed:", len(rows))
            print("Inserted:", inserted)
            print("Skipped:", skipped)
            print()

            total += inserted

    print("DONE")
    print("Total inserted:", total)
    print("Database:", DATABASE_FILE)


if __name__ == "__main__":
    main()