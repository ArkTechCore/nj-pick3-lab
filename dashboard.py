import streamlit as st
from pathlib import Path

st.set_page_config(
    page_title="NJ Pick3 Lab",
    page_icon="🎯",
    layout="wide"
)

REPORTS_DIR = Path("data/reports")
AI_FILE = REPORTS_DIR / "PHASE_13_GROQ_AI_ANALYSIS.txt"

st.title("🎯 NJ Pick3 Lab Dashboard")
st.caption("Historical analytics, candidates, and AI summary")

st.warning("Lottery results are random. This dashboard shows historical patterns only.")

st.header("AI Analysis")

if AI_FILE.exists():
    st.text(AI_FILE.read_text(encoding="utf-8"))
else:
    st.error("AI analysis file not found. Run the pipeline first.")

st.header("Reports")

for file in REPORTS_DIR.glob("*"):
    st.write(file.name)