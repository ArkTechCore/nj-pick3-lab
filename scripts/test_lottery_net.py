import re
import pandas as pd

url = "https://www.lottery.net/new-jersey/pick-3-evening/results/2024"

df = pd.read_html(url)[0]

print(df.head())

for _, row in df.head(10).iterrows():
    date = pd.to_datetime(row["Result Date"])
    digits = re.findall(r"\d", str(row["Results"]))
    number = "".join(digits[:3])
    fireball = digits[3] if len(digits) > 3 else ""

    print(date.date(), number, "fireball:", fireball)