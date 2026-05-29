import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import *
print("Base:", BASE_DIR)
print("Database:", DATABASE_FILE)
print("Raw:", RAW_DIR)
print("Reports:", REPORTS_DIR)
