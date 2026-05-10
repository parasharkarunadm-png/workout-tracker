import streamlit as st
import pandas as pd
import plotly.express as px
from db import SessionLocal, Program, ProgramDay, ProgramSet, Exercise, Session, LoggedSet
from sqlalchemy import func


# ---------------------------------------------------------------------------
# DB reads
# ---------------------------------------------------------------------------
def get_programs():
    db = SessionLocal()
    programs = db.query(Program).all()
    db.close()
    return programs


def get_exercises_for_program(program_id: int) -> list:
    """Return distinct exercises in a program with set counts."""
    db = SessionLocal()
    results = (
        db.query(Exercise)
        .join(ProgramSet, ProgramSet.exercise_id == Exercise.id)
        .join(ProgramDay, ProgramDay.id == ProgramSet.day_id)
        .filter(ProgramDay.program_id == program_id)
        .distinct()
        .order_by(Exercise.name)
        .all()
    )
    exercises = [{"id": ex.id, "name": ex.name} for ex in results]
    db.close()
    return exercises


def get_load_trend(exercise_id: int) -> pd.DataFrame:
    """Top set weight per session for an exercise — excludes warmups and empty sessions."""
    db = SessionLocal()
    results = (
        db.query(
            Session.date,
            func.max(LoggedSet.weight_lb).label("top_weight"),
            func.max(LoggedSet.reps).label("reps_at_top"),
        )
        .join(LoggedSet, LoggedSet.session_id == Session.id)
        .filter(
            LoggedSet.exercise_id == exercise_id,
            LoggedSet.set_type.in_(["working", "amrap"]),
        )
        .group_by(Session.id, Session.date)
        .having(func.count(LoggedSet.id) > 0)
        .order_by(Session.date)
        .all()
    )
    db.close()

    if not results:
        return pd.DataFrame()

    return pd.DataFrame([{
        "date"      : r.date.strftime("%Y-%m-%d"),
        "top_weight": r.top_weight,
        "reps"      : r.reps_at_top,
    } for r in results])


def get_rest_intervals(exercise_id: int) -> pd.DataFrame:
    """Average rest per session for an exercise."""
    db = SessionLocal()
    results = (
        db.query(
            Session.date,
            func.avg(LoggedSet.rest_secs).label("avg_rest"),
        )
        .join(LoggedSet, LoggedSet.session_id == Session.id)
        .filter(
            LoggedSet.exercise_id == exercise_id,
            LoggedSet.rest_secs   != None,
            LoggedSet.rest_secs   > 0,
        )
        .group_by(Session.id, Session.date)
        .having(func.count(LoggedSet.id) > 0)
        .order_by(Session.date)
        .all()
    )
    db.close()

    if not results:
        return pd.DataFrame()

    return pd.DataFrame([{
        "date"    : r.date.strftime("%Y-%m-%d"),
        "avg_rest": round(r.avg_rest / 60, 2),  # convert to minutes
    } for r in results])


def get_pr_history(exercise_id: int) -> pd.DataFrame:
    """All PR sets for an exercise."""
    db = SessionLocal()
    results = (
        db.query(LoggedSet, Session.date)
        .join(Session, Session.id == LoggedSet.session_id)
        .filter(
            LoggedSet.exercise_id == exercise_id,
            LoggedSet.is_pr       == True,
        )
        .order_by(Session.date)
        .all()
    )

    return pd.DataFrame([{
        "date"     : sess.strftime("%Y-%m-%d"),
        "weight_lb": ls.weight_lb,
        "reps"     : ls.reps,
        "set_type" : ls.set_type,
    } for ls, sess in results])


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------
def render():
    st.title("Analytics")

    programs = get_programs()
    if not programs:
        st.warning("No programs found. Import one first via Admin.")
        return

    # --- Program selector ---
    program_map     = {p.name: p.id for p in programs}
    selected_program = st.selectbox("Program", list(program_map.keys()))
    program_id       = program_map[selected_program]

    exercises = get_exercises_for_program(program_id)
    if not exercises:
        st.warning("No exercises found for this program.")
        return

    # --- Exercise selector ---
    exercise_map     = {ex["name"]: ex["id"] for ex in exercises}
    selected_exercise = st.selectbox("Exercise", list(exercise_map.keys()))
    exercise_id       = exercise_map[selected_exercise]

    st.divider()

    # --- Load trend ---
    st.subheader("Load Trend")
    df_load = get_load_trend(exercise_id)
    if df_load.empty:
        st.info("No working sets logged yet for this exercise.")
    else:
        fig = px.line(
            df_load, x="date", y="top_weight",
            markers=True,
            labels={"date": "Date", "top_weight": "Top Set (lb)"},
            hover_data=["reps"],
        )
        fig.update_layout(
            plot_bgcolor="#1a1a2e",
            paper_bgcolor="#0e1117",
            font_color="#fafafa",
            margin=dict(l=0, r=0, t=0, b=0),
        )
        fig.update_traces(line_color="#4da6ff", marker_color="#4da6ff")
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # --- Rest intervals ---
    st.subheader("Avg Rest Per Session (mins)")
    df_rest = get_rest_intervals(exercise_id)
    if df_rest.empty:
        st.info("No rest data logged yet for this exercise.")
    else:
        fig2 = px.bar(
            df_rest, x="date", y="avg_rest",
            labels={"date": "Date", "avg_rest": "Avg Rest (mins)"},
        )
        fig2.update_layout(
            plot_bgcolor="#1a1a2e",
            paper_bgcolor="#0e1117",
            font_color="#fafafa",
            margin=dict(l=0, r=0, t=0, b=0),
        )
        fig2.update_traces(marker_color="#4da6ff")
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()

    # --- PR history ---
    st.subheader("PR History")
    df_pr = get_pr_history(exercise_id)
    if df_pr.empty:
        st.info("No PRs recorded for this exercise yet.")
    else:
        st.dataframe(
            df_pr.rename(columns={
                "date"     : "Date",
                "weight_lb": "Weight (lb)",
                "reps"     : "Reps",
                "set_type" : "Set Type",
            }),
            use_container_width=True,
            hide_index=True,
        )