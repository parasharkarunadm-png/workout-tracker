import streamlit as st
from datetime import datetime
from db import SessionLocal, Program, ProgramDay, Session, LoggedSet


# ---------------------------------------------------------------------------
# Helpers — timers
# ---------------------------------------------------------------------------
def fmt_duration(seconds: int) -> str:
    """Format seconds into HH:MM:SS string."""
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02}:{m:02}:{s:02}"


def get_day_label(program_day_id: int) -> str:
    db = SessionLocal()
    day = db.query(ProgramDay).filter(ProgramDay.id == program_day_id).first()
    db.close()
    return day.label if day else "Unknown Day"


# ---------------------------------------------------------------------------
# Screen 2 — sticky header
# ---------------------------------------------------------------------------
def screen_logger():
    now = datetime.utcnow()

    # --- Compute durations ---
    session_start = st.session_state.get("session_start_time")
    last_set_time = st.session_state.get("last_set_time")
    first_set_logged = st.session_state.get("first_set_logged", False)

    session_secs = int((now - session_start).total_seconds()) if session_start else 0
    rest_secs    = int((now - last_set_time).total_seconds()) if (last_set_time and first_set_logged) else 0

    day_label = get_day_label(st.session_state.program_day_id)

    # --- Sticky header ---
    st.markdown(f"### {day_label}")
    col1, col2, col3 = st.columns([2, 2, 2])
    col1.metric("Session", fmt_duration(session_secs))
    col2.metric("Rest", fmt_duration(rest_secs) if first_set_logged else "--:--:--")
    col3.empty()

    if st.button("Finish Session", type="primary", use_container_width=True):
        db = SessionLocal()
        session = db.query(Session).filter(Session.id == st.session_state.session_id).first()
        if session:
            session.duration_mins = session_secs // 60
            db.commit()
        db.close()
        st.session_state.session_started  = False
        st.session_state.session_id       = None
        st.session_state.program_day_id   = None
        st.session_state.last_set_time    = None
        st.session_state.session_start_time = None
        st.session_state.first_set_logged = False
        st.rerun()

    st.divider()
    st.info("Exercise logger coming next.")


# ---------------------------------------------------------------------------
# Helper — load programs from db
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
        .filter(
            ProgramDay.program_id == program_id,
            ProgramDay.week_num == week_num,
        )
        .order_by(ProgramDay.day_num)
        .all()
    )
    db.close()
    return days


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

    # --- Program selector ---
    program_map = {p.name: p.id for p in programs}
    selected_program_name = st.selectbox("Program", list(program_map.keys()))
    selected_program_id = program_map[selected_program_name]

    # --- Week selector ---
    weeks = get_weeks(selected_program_id)
    if not weeks:
        st.warning("This program has no weeks defined yet.")
        return

    selected_week = st.selectbox(
        "Week",
        weeks,
        format_func=lambda w: f"Week {w}",
    )

    # --- Day selector by label ---
    days = get_days(selected_program_id, selected_week)
    if not days:
        st.warning("No days found for this week.")
        return

    day_map = {d.label: d.id for d in days}
    selected_day_label = st.selectbox("Day", list(day_map.keys()))
    selected_day_id = day_map[selected_day_label]

    st.divider()

    # --- Start session ---
    if st.button("Start Session", type="primary", use_container_width=True):
        session_id = create_session(selected_day_id)
        st.session_state.session_id          = session_id
        st.session_state.program_day_id      = selected_day_id
        st.session_state.session_started     = True
        st.session_state.last_set_time       = None
        st.session_state.session_start_time  = datetime.utcnow()
        st.session_state.first_set_logged    = False
        st.rerun()


# ---------------------------------------------------------------------------
# Entry point — called from app.py
# ---------------------------------------------------------------------------
def render():
    if not st.session_state.session_started:
        screen_select_day()
    else:
        screen_logger()