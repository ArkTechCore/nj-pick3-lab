import sys
import sqlite3
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from config import DATABASE_FILE

conn = sqlite3.connect(DATABASE_FILE)

rows = conn.execute("""
SELECT
    substr(draw_date,1,4) as year,
    count(*) as total
FROM draws
GROUP BY year
ORDER BY year
""").fetchall()

print("\nYears in database:\n")

for year, total in rows:
    print(f"{year}: {total}")

conn.close()