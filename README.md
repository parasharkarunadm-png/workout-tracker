# workout-tracker
Light weight web app to replicate functionalities of the popular workout app Macrofactor-workouts

--A personal workout logging web app built with Streamlit and SQLite.
--Tracks programs, sets, rest intervals, load progression, and PRs.

---

## Stack

- **Framework**: Streamlit
- **Database**: SQLite via SQLAlchemy
- **Charts**: Plotly
- **Data parsing**: pandas + openpyxl
- **Hosting**: Streamlit Community Cloud (free tier)

---

## Setup

### Prerequisites

- Python 3.11+
- Git
- VS Code with extensions: Python, Pylance, SQLite Viewer, GitLens

### Install

```bash
git clone https://github.com/YOUR_USERNAME/workout-tracker.git
cd workout-tracker
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Initialize database

```bash
python -c "from db import init_db; init_db()"
python seed.py
```

### Run locally

```bash
streamlit run app.py
```

---

## Project Structure

```
workout-tracker/
├── app.py              # Entry point, page routing, session state defaults
├── db.py               # SQLAlchemy models and database initialization
├── log_workout.py      # Workout logging UI (Screen 1 + Screen 2)
├── importer.py         # Program import from Excel template
├── seed.py             # Exercise library seed script
├── list_exercises.py   # Print all exercises in the database
├── phat_import.xlsx    # PHAT program import template (Week 1)
├── requirements.txt    # Python dependencies
└── workout.db          # SQLite database (gitignored)
```

---

## Importing a Program

Programs are imported from a flat Excel file with this exact column structure:

```
week | day_num | day_label | exercise_name | set_num | target_reps | target_rir | target_pct_1rm | notes
```

Rules:
- One row per set
- `exercise_name` must match exactly what's in the `exercises` table — run `python list_exercises.py` to see valid names
- Leave `target_reps` blank for AMRAP sets
- Leave `target_pct_1rm` blank for hypertrophy sets (e.g. 0.70 for 70% of 1RM)

To import:
```bash
python importer.py
```

The importer validates all exercise names before writing anything. If names don't match, it prints a list of unmatched names and exits without importing.

---

## Data Model

```
exercises        — exercise library (name, muscle, equipment, movement pattern)
programs         — named program with source reference
program_days     — week/day structure with label (e.g. "Upper Body Power")
program_sets     — planned sets per exercise per day (target reps, RIR, % 1RM)
sessions         — one gym visit tied to a program day
logged_sets      — actual sets logged (weight_lb, reps, RIR, rest_secs, is_pr)
```

Key design decisions:
- `weight_lb` used throughout — no unit conversion
- `program_set_id` in `logged_sets` is nullable — null means ad-hoc set
- `target_pct_1rm` in `program_sets` is nullable — used for percentage-based programs like PHAT
- PR logic: heavier weight than ever logged, OR more reps at the current top weight

---

## Development Log

Each step below was built incrementally and verified working before proceeding.

---

### Step 1 — Environment Setup
**Files**: none (local only)

- Installed Python 3.11+, VS Code, Git on Mac
- VS Code extensions: Python, Pylance, SQLite Viewer, GitLens
- Created project folder, Python venv, activated with `source venv/bin/activate`
- Installed dependencies: `pip install streamlit sqlalchemy pandas plotly openpyxl`
- Froze dependencies: `pip freeze > requirements.txt`
- Created GitHub repo, connected remote, pushed initial commit
- Verified: `streamlit run app.py` opened in browser at `localhost:8501`

---

### Step 2 — Database Schema
**Files**: `db.py`

- Defined 6 SQLAlchemy models: `Exercise`, `Program`, `ProgramDay`, `ProgramSet`, `Session`, `LoggedSet`
- Key decisions locked in:
  - `weight_lb` for all weight storage (no kg)
  - `program_set_id` nullable in `logged_sets` (supports ad-hoc sets)
  - `target_pct_1rm` nullable in `program_sets` (percentage-based loading)
  - `set_type` column: working / warmup / failure / drop
- Created `init_db()` and `get_db()` helpers
- Verified: `python -c "from db import init_db; init_db()"` created `workout.db` with all 6 tables visible in SQLite Viewer

---

### Step 3 — Exercise Seed
**Files**: `seed.py`, `list_exercises.py`

- Seeded 30 base exercises across: chest, back, shoulders, triceps, biceps, quads, hamstrings, glutes, calves
- Each exercise tagged with: `primary_muscle`, `equipment`, `movement_pattern`
- Equipment types: barbell, dumbbell, cable, machine, bodyweight
- Movement patterns: push, pull, hinge, squat, isolation
- Script is idempotent — safe to re-run, checks by name before inserting
- Expanded to 55 exercises after reading PHAT program from Liftvault, adding PHAT-specific exercises
- `list_exercises.py` added as a helper to print all valid exercise names (used during import validation)
- Verified: `python seed.py` showed 55 exercises in SQLite Viewer

---

### Step 4 — Schema Updates
**Files**: `db.py`

- Added `target_pct_1rm` column to `ProgramSet`
- Renamed weight column to `weight_lb` throughout (from earlier `weight_kg` iterations)
- Rebuilt database cleanly: `rm workout.db && python -c "from db import init_db; init_db()" && python seed.py`
- Verified: 55 exercises restored, correct column names confirmed in SQLite Viewer

---

### Step 5 — App Shell
**Files**: `app.py`

- Configured Streamlit page: centered layout, collapsed sidebar, 🏋️ icon
- `init_db()` called on every startup (safe — skips if tables exist)
- Session state defaults initialized with idempotent pattern:
  ```python
  if key not in st.session_state:
      st.session_state[key] = val
  ```
- Defaults: `session_started`, `session_id`, `program_day_id`, `last_set_time`,
  `session_start_time`, `first_set_logged`, `logged_sets`, `adhoc_sets`,
  `adhoc_counter`, `last_logged_key`
- Sidebar navigation: Log Workout / Programs / Analytics
- Verified: three pages load, navigation switches between them, no errors

---

### Step 6 — Screen 1: Program Day Selector
**Files**: `log_workout.py`

- Dropdown chain: Program → Week → Day (by label, not number)
- Day labels come from `program_days.label` — fully dynamic per program
- Start Session button:
  - Creates a `Session` row in the database
  - Sets `session_started = True` in session state
  - Records `session_start_time`
  - Triggers `st.rerun()` to transition to Screen 2
- Verified: "No programs found" warning shows correctly with empty database; session creation confirmed after import

---

### Step 7 — Program Importer
**Files**: `importer.py`, `phat_import.xlsx`

- Reads flat Excel template with pandas + openpyxl
- Validates all exercise names against database before writing anything — exits with unmatched list if any fail
- Duplicate program name check — safe to re-run after fixing names
- Creates `Program`, `ProgramDay`, and `ProgramSet` rows in dependency order
- PHAT imported as Week 1 (repeating base week); weeks 2–4 with progressive percentages planned for Sprint 3
- Verified: `python importer.py` reported correct week/day/set counts; Screen 1 showed PHAT program and day labels

---

### Step 8 — Screen 2: Sticky Header
**Files**: `log_workout.py`

- Shows day label, Session timer (total elapsed), Rest timer (since last logged set)
- Rest timer shows `--:--:--` until first set is logged
- Finish Session button:
  - Writes `duration_mins` to the `sessions` row
  - Clears all session state keys
  - Returns to Screen 1
- Timers update on every Streamlit rerun (on interaction), not in real time — acceptable for gym use
- Verified: session timer counted up correctly; Finish Session returned to Screen 1 cleanly

---

### Step 9 — Exercise List Display
**Files**: `log_workout.py`

- `get_planned_exercises()` loads all exercises and their planned sets for today's program day
- `get_last_best_set()` queries the most recent session for each exercise, finds the max weight set, displays as: `Last best: 185lb × 5 reps`
- Shows "No previous data" on first ever session for an exercise
- Target reps and % 1RM shown per set (e.g. `Target: 5 reps @ 70% 1RM`)
- AMRAP sets show "AMRAP" instead of a rep number (stored as `None` in `program_sets.target_reps`)
- Verified: Upper Body Power day displayed all 9 exercises with correct set targets and percentages

---

### Step 10 — Log Set
**Files**: `log_workout.py`

- Input fields per set: weight (lb), reps (pre-filled from target), RIR (pre-filled from target)
- Weight field defaults to empty (`value=None`) — no clearing required before typing
- Log button guard: warns and stops if weight is empty
- On log:
  - Writes `LoggedSet` row to database via `log_set()`
  - Stores result in `st.session_state.logged_sets[psid]` including `db_id`
  - Updates `last_set_time` for rest timer
  - Sets `first_set_logged = True`
  - Triggers rerun
- Logged sets render as green summary line (Option A):
  ```
  ✅ Set 1 — 185lb × 5 reps @ RIR 2 | Rest: 01:45
  ```
- PR badge 🏆 shown on summary line when applicable
- Verified: sets logged correctly, database rows confirmed in SQLite Viewer, summary lines rendered correctly

---

### Step 11 — Ad-hoc Sets
**Files**: `log_workout.py`, `app.py`

- ➕ Add Set button below each exercise's planned sets
- Ad-hoc sets use negative integer keys in session state (`-1`, `-2`, ...) to avoid collision with `program_set_id` values
- `adhoc_sets` dict in session state: `exercise_id -> [key1, key2, ...]`
- `adhoc_counter` decrements by 1 per new ad-hoc set
- Ad-hoc sets written to `logged_sets` with `program_set_id = None`
- Logging flow identical to planned sets via shared `handle_log()` function
- Verified: Add Set button appeared, ad-hoc set logged correctly, green summary line showed "(ad-hoc)" label

---

### Step 12 — Undo Last Set
**Files**: `log_workout.py`, `app.py`

- `last_logged_key` tracked in session state — set by `handle_log()` after every successful log
- ↩️ Undo Last Set button appears only when `last_logged_key` is not None
- `undo_last_set()`:
  - Pops the set from `st.session_state.logged_sets`
  - Deletes the corresponding row from the database using `db_id`
  - Removes from `adhoc_sets` if it was an ad-hoc set
  - Resets `last_logged_key` and `last_set_time`
- Only one level of undo (last set only) — by design
- Verified: undo button appeared after logging, green row disappeared on undo, database row deleted confirmed in SQLite Viewer

---

### Step 13 — PR Logic
**Files**: `log_workout.py`

- Two-condition PR check in `log_set()`:
  1. No previous data for this exercise → PR (first ever set)
  2. Weight is heavier than any previously logged set → weight PR
  3. Weight equals current top weight AND reps exceed best reps at that weight → rep PR
- PR flag stored as `is_pr` boolean in `logged_sets`
- 🏆 badge shown on summary line when `is_pr = True`
- Verified: repeated same weight/reps not flagged as PR; heavier weight correctly flagged

---

## Upcoming (Sprint 3+)

- Session summary screen on Finish
- Streamlit Community Cloud deployment
- Programs page with import UI
- PHAT weeks 2–4 with progressive percentages
- Analytics: load trend, volume trend, rest interval, stall detection
- Exercise swap with muscle/movement filter + search
- Full exercise library expansion to 150–200 exercises
- Data export to CSV