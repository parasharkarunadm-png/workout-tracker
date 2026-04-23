import streamlit as st
from datetime import datetime
from db import SessionLocal, Program, ProgramDay, Session


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
        st.session_state.session_id     = session_id
        st.session_state.program_day_id = selected_day_id
        st.session_state.session_started = True
        st.session_state.last_set_time  = datetime.utcnow()
        st.rerun()


# ---------------------------------------------------------------------------
# Entry point — called from app.py
# ---------------------------------------------------------------------------
def render():
    if not st.session_state.session_started:
        screen_select_day()
    else:
        st.info("Screen 2 — Logger coming next.")
        if st.button("End Session (placeholder)"):
            st.session_state.session_started = False
            st.session_state.session_id      = None
            st.session_state.program_day_id  = None
            st.rerun()