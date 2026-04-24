import streamlit as st
from datetime import datetime
from db import SessionLocal, Program, ProgramDay, Session, LoggedSet


# ---------------------------------------------------------------------------
# Helpers — formatting
# ---------------------------------------------------------------------------
def fmt_duration(seconds: int) -> str:
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02}:{m:02}:{s:02}"


# ---------------------------------------------------------------------------
# DB reads
# ---------------------------------------------------------------------------
def get_programs():
    db = SessionLocal()
    programs = db.query(Program).all()
    db.close()
    return programs


def get_weeks(program_id):
    db = SessionLocal()
    weeks = (
        db.query(ProgramDay.week_num)
        .filter(ProgramDay.program_id == program_id)
        .distinct()
        .order_by(ProgramDay.week_num)
        .all()
    )
    db.close()
    return [w.week_num for w in weeks]


def get_days(program_id, week_num):
    db = SessionLocal()
    days = (
        db.query(ProgramDay)
        .filter(ProgramDay.program_id == program_id,
                ProgramDay.week_num == week_num)
        .order_by(ProgramDay.day_num)
        .all()
    )
    db.close()
    return days


def get_day_label(program_day_id: int) -> str:
    db = SessionLocal()
    day = db.query(ProgramDay).filter(ProgramDay.id == program_day_id).first()
    db.close()
    return day.label if day else "Unknown Day"


def get_planned_exercises(program_day_id: int) -> list:
    db = SessionLocal()
    day = db.query(ProgramDay).filter(ProgramDay.id == program_day_id).first()
    if not day:
        db.close()
        return []

    exercises = {}
    for ps in sorted(day.sets, key=lambda x: (x.set_num, x.exercise_id)):
        ex = ps.exercise
        if ex.id not in exercises:
            exercises[ex.id] = {
                "exercise_id"  : ex.id,
                "exercise_name": ex.name,
                "sets"         : [],
            }
        exercises[ex.id]["sets"].append({
            "program_set_id": ps.id,
            "set_num"       : ps.set_num,
            "target_reps"   : ps.target_reps,
            "target_rir"    : ps.target_rir,
            "target_pct_1rm": ps.target_pct_1rm,
            "notes"         : ps.notes,
        })

    db.close()
    return list(exercises.values())


def get_last_best_set(exercise_id: int, current_session_id: int) -> str:
    db = SessionLocal()
    last = (
        db.query(LoggedSet)
        .filter(LoggedSet.exercise_id == exercise_id,
                LoggedSet.session_id  != current_session_id)
        .order_by(LoggedSet.logged_at.desc())
        .all()
    )
    db.close()

    if not last:
        return "No previous data"

    most_recent_session = last[0].session_id
    session_sets = [s for s in last if s.session_id == most_recent_session]
    best = max(session_sets, key=lambda s: s.weight_lb)
    return f"Last best: {best.weight_lb}lb × {best.reps} reps"


# ---------------------------------------------------------------------------
# DB write
# ---------------------------------------------------------------------------
def log_set(session_id, exercise_id, program_set_id, set_num,
            weight_lb, reps, rir, rest_secs):
    """Write one logged set. Returns (is_pr, db_id)."""
    db = SessionLocal()

    # Step 1 — find heaviest weight ever logged for this exercise
    prev_best_weight = (
        db.query(LoggedSet)
        .filter(LoggedSet.exercise_id == exercise_id)
        .order_by(LoggedSet.weight_lb.desc())
        .first()
    )

    if prev_best_weight is None:
        is_pr = True  # first ever set
    elif weight_lb > prev_best_weight.weight_lb:
        is_pr = True  # heavier than ever
    else:
        # Step 2 — check rep PR at the top weight
        best_reps_at_top = (
            db.query(LoggedSet)
            .filter(LoggedSet.exercise_id == exercise_id,
                    LoggedSet.weight_lb   == prev_best_weight.weight_lb)
            .order_by(LoggedSet.reps.desc())
            .first()
        )
        is_pr = (
            weight_lb == prev_best_weight.weight_lb and
            reps > best_reps_at_top.reps
        )

    entry = LoggedSet(
        session_id     = session_id,
        exercise_id    = exercise_id,
        program_set_id = program_set_id,
        set_num        = set_num,
        weight_lb      = weight_lb,
        reps           = reps,
        rir            = rir,
        rest_secs      = rest_secs,
        is_pr          = is_pr,
        set_type       = "working",
        logged_at      = datetime.utcnow(),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    db_id = entry.id
    db.close()
    return is_pr, db_id


# ---------------------------------------------------------------------------
# Undo helper
# ---------------------------------------------------------------------------
def undo_last_set():
    key = st.session_state.last_logged_key
    if key is None:
        return

    logged = st.session_state.logged_sets.pop(key, None)
    if logged and logged.get("db_id"):
        db = SessionLocal()
        entry = db.query(LoggedSet).filter(LoggedSet.id == logged["db_id"]).first()
        if entry:
            db.delete(entry)
            db.commit()
        db.close()

    # Remove from adhoc_sets if applicable
    for ex_id, keys in st.session_state.adhoc_sets.items():
        if key in keys:
            keys.remove(key)
            break

    st.session_state.last_logged_key  = None
    st.session_state.first_set_logged = len(st.session_state.logged_sets) > 0
    st.session_state.last_set_time    = None


# ---------------------------------------------------------------------------
# Shared log button handler
# ---------------------------------------------------------------------------
def handle_log(key, exercise_id, program_set_id, set_num, weight, reps, rir):
    """Called when any Log button is tapped. Updates state and db."""
    now       = datetime.utcnow()
    last_time = st.session_state.last_set_time
    rest_secs = int((now - last_time).total_seconds()) if last_time else 0

    is_pr, db_id = log_set(
        session_id     = st.session_state.session_id,
        exercise_id    = exercise_id,
        program_set_id = program_set_id,
        set_num        = set_num,
        weight_lb      = weight,
        reps           = reps,
        rir            = rir if rir is not None else 0,
        rest_secs      = rest_secs,
    )

    st.session_state.logged_sets[key] = {
        "weight_lb": weight,
        "reps"     : reps,
        "rir"      : rir if rir is not None else 0,
        "rest_secs": rest_secs,
        "is_pr"    : is_pr,
        "db_id"    : db_id,
    }
    st.session_state.last_logged_key  = key
    st.session_state.last_set_time    = now
    st.session_state.first_set_logged = True


# ---------------------------------------------------------------------------
# Session create
# ---------------------------------------------------------------------------
def create_session(program_day_id):
    db = SessionLocal()
    new_session = Session(
        program_day_id=program_day_id,
        date=datetime.utcnow(),
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    session_id = new_session.id
    db.close()
    return session_id


# ---------------------------------------------------------------------------
# Screen 1 — Program day selector
# ---------------------------------------------------------------------------
def screen_select_day():
    st.subheader("Select Today's Workout")
    programs = get_programs()

    if not programs:
        st.warning("No programs found. Go to Programs to import one first.")
        return

    program_map = {p.name: p.id for p in programs}
    selected_program_name = st.selectbox("Program", list(program_map.keys()))
    selected_program_id   = program_map[selected_program_name]

    weeks = get_weeks(selected_program_id)
    if not weeks:
        st.warning("This program has no weeks defined yet.")
        return

    selected_week = st.selectbox("Week", weeks, format_func=lambda w: f"Week {w}")

    days = get_days(selected_program_id, selected_week)
    if not days:
        st.warning("No days found for this week.")
        return

    day_map            = {d.label: d.id for d in days}
    selected_day_label = st.selectbox("Day", list(day_map.keys()))
    selected_day_id    = day_map[selected_day_label]

    st.divider()

    if st.button("Start Session", type="primary", use_container_width=True):
        session_id = create_session(selected_day_id)
        st.session_state.session_id         = session_id
        st.session_state.program_day_id     = selected_day_id
        st.session_state.session_started    = True
        st.session_state.last_set_time      = None
        st.session_state.session_start_time = datetime.utcnow()
        st.session_state.first_set_logged   = False
        st.rerun()


# ---------------------------------------------------------------------------
# Screen 2 — Logger
# ---------------------------------------------------------------------------
def screen_logger():
    now = datetime.utcnow()

    session_start    = st.session_state.get("session_start_time")
    last_set_time    = st.session_state.get("last_set_time")
    first_set_logged = st.session_state.get("first_set_logged", False)

    session_secs = int((now - session_start).total_seconds()) if session_start else 0
    rest_secs_hdr = int((now - last_set_time).total_seconds()) if (last_set_time and first_set_logged) else 0

    day_label = get_day_label(st.session_state.program_day_id)

    # --- Sticky header ---
    st.markdown(f"### {day_label}")
    col1, col2 = st.columns(2)
    col1.metric("Session", fmt_duration(session_secs))
    col2.metric("Rest", fmt_duration(rest_secs_hdr) if first_set_logged else "--:--:--")

    if st.button("Finish Session", type="primary", use_container_width=True):
        db = SessionLocal()
        s = db.query(Session).filter(Session.id == st.session_state.session_id).first()
        if s:
            s.duration_mins = session_secs // 60
            db.commit()
        db.close()
        for key in ["session_started", "session_id", "program_day_id",
                    "last_set_time", "session_start_time", "first_set_logged",
                    "logged_sets", "adhoc_sets", "adhoc_counter", "last_logged_key"]:
            st.session_state[key] = {
                "session_started" : False,
                "session_id"      : None,
                "program_day_id"  : None,
                "last_set_time"   : None,
                "session_start_time": None,
                "first_set_logged": False,
                "logged_sets"     : {},
                "adhoc_sets"      : {},
                "adhoc_counter"   : -1,
                "last_logged_key" : None,
            }[key]
        st.rerun()

    if st.session_state.last_logged_key is not None:
        if st.button("↩️ Undo Last Set", use_container_width=True):
            undo_last_set()
            st.rerun()

    st.divider()

    # --- Exercises ---
    exercises = get_planned_exercises(st.session_state.program_day_id)
    if not exercises:
        st.warning("No exercises found for this program day.")
        return

    for ex in exercises:
        eid       = ex["exercise_id"]
        last_best = get_last_best_set(eid, st.session_state.session_id)

        st.markdown(f"#### {ex['exercise_name']}")
        st.caption(last_best)

        # Planned sets
        for s in ex["sets"]:
            psid      = s["program_set_id"]
            rep_label = "AMRAP" if s["target_reps"] is None else str(s["target_reps"])
            pct_label = f" @ {int(s['target_pct_1rm']*100)}% 1RM" if s["target_pct_1rm"] else ""

            if psid in st.session_state.logged_sets:
                logged   = st.session_state.logged_sets[psid]
                pr_badge = " 🏆 PR" if logged.get("is_pr") else ""
                rest_str = f" | Rest: {fmt_duration(logged['rest_secs'])}" if logged["rest_secs"] else ""
                st.success(f"✅ Set {s['set_num']} — {logged['weight_lb']}lb × {logged['reps']} reps @ RIR {logged['rir']}{rest_str}{pr_badge}")
                continue

            st.markdown(f"**Set {s['set_num']}** — Target: {rep_label} reps{pct_label}")
            c1, c2, c3, c4 = st.columns([2, 2, 2, 2])
            weight = c1.number_input("lb",   min_value=0.0, step=0.5, value=None, placeholder="lb",   key=f"weight_{psid}")
            reps   = c2.number_input("Reps", min_value=0,              value=s["target_reps"] if s["target_reps"] else None, placeholder="Reps", key=f"reps_{psid}")
            rir    = c3.number_input("RIR",  min_value=0,              value=s["target_rir"]  if s["target_rir"]  else None, placeholder="RIR",  key=f"rir_{psid}")

            if c4.button("Log", key=f"log_{psid}"):
                if weight is None:
                    st.warning("Enter weight before logging.")
                    st.stop()
                try:
                    handle_log(psid, eid, psid, s["set_num"], weight, reps, rir)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

        # Ad-hoc sets
        adhoc_keys    = st.session_state.adhoc_sets.get(eid, [])
        adhoc_set_num = len(ex["sets"]) + 1

        for akey in adhoc_keys:
            if akey in st.session_state.logged_sets:
                logged   = st.session_state.logged_sets[akey]
                pr_badge = " 🏆 PR" if logged.get("is_pr") else ""
                rest_str = f" | Rest: {fmt_duration(logged['rest_secs'])}" if logged["rest_secs"] else ""
                st.success(f"✅ Set {adhoc_set_num} (ad-hoc) — {logged['weight_lb']}lb × {logged['reps']} reps @ RIR {logged['rir']}{rest_str}{pr_badge}")
            else:
                st.markdown(f"**Set {adhoc_set_num}** — Ad-hoc")
                c1, c2, c3, c4 = st.columns([2, 2, 2, 2])
                weight = c1.number_input("lb",   min_value=0.0, step=0.5, value=None, placeholder="lb",   key=f"weight_{akey}")
                reps   = c2.number_input("Reps", min_value=0,              value=None, placeholder="Reps", key=f"reps_{akey}")
                rir    = c3.number_input("RIR",  min_value=0,              value=None, placeholder="RIR",  key=f"rir_{akey}")

                if c4.button("Log", key=f"log_{akey}"):
                    if weight is None:
                        st.warning("Enter weight before logging.")
                        st.stop()
                    try:
                        handle_log(akey, eid, None, adhoc_set_num, weight, reps, rir)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

            adhoc_set_num += 1

        if st.button("➕ Add Set", key=f"add_{eid}"):
            akey = st.session_state.adhoc_counter
            st.session_state.adhoc_counter -= 1
            if eid not in st.session_state.adhoc_sets:
                st.session_state.adhoc_sets[eid] = []
            st.session_state.adhoc_sets[eid].append(akey)
            st.rerun()

        st.divider()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def render():
    if not st.session_state.session_started:
        screen_select_day()
    else:
        screen_logger()