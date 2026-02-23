# MIFA Judge Assistant

A Streamlit app for first-time MIFA (Michigan Interscholastic Forensic Association) speech tournament judges. Built to handle the complexity of 16 event categories so you can focus on the students, not the paperwork.

## What It Does

- **Event Reference** — Rules, timing, judging criteria, dos/don'ts for all 16 MIFA events (9 Oral Interpretation + 7 Public Address)
- **Live Timer & Stopwatch** — Hybrid Python/JavaScript countdown that runs independently of Streamlit reruns, with overtime tracking
- **Structured Note-Taking** — Critique sheets matching the official MIFA ballot format with category-specific criteria (Quality of Literature, Vocal Performance, Organization, etc.)
- **Interactive Feedback Starters** — Sentence-starter phrases you select and personalize, so every student gets individualized comments
- **MIFA-Compliant Scoring** — Built-in validation (rank 1 = 100%, no duplicate percentages, 75-100 range, rank order matches percentage order)
- **Tabroom Export** — Copy-ready ranked summary and per-student feedback blocks
- **Auto-Save & Round History** — JSON persistence with browse/reload of past rounds

## Quick Start

```bash
cd mifa-judge-app
pip install -r requirements.txt
streamlit run app.py
```

Open http://localhost:8501, select an event, enter student names, and start judging.

## How It Works

1. **Sidebar** — Pick your event, enter student count and names, start the round
2. **Judge tab** — Fill in ballot info, start/stop timer per student, take notes using criteria fields and feedback starters
3. **Scores tab** — Enter ranks (1-4) and percentages (75-100) with live validation
4. **Summary tab** — Review ranked results, copy formatted output for Tabroom

## Project Structure

```
app.py                 # Main Streamlit app
event_data.py          # 16 event definitions (rules, criteria, dos/don'ts)
timer_component.py     # Hybrid Python + JavaScript timer
scoring_engine.py      # MIFA scoring validation
data_manager.py        # JSON save/load and export formatting
tests/                 # pytest test suite (353 tests)
data/rounds/           # Auto-saved round JSON files
```

## Events Covered

**Oral Interpretation:** Dramatic Interp, Duo Interp, Multiple Interp, Poetry Interp, Program Oral Interp (POI), Prose Interp, Storytelling, OI Poetry, OI Prose

**Public Address:** Broadcasting, Duo Commentary, Extemporaneous Speaking, Impromptu, Informative Speaking, Oratory, Sales Speaking

## Running Tests

```bash
pytest tests/ -v
```

## Built With

- [Streamlit](https://streamlit.io/)
- [Claude Code](https://claude.ai/claude-code)
