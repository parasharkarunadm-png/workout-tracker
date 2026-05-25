import pandas as pd
from sqlalchemy import func
from db import SessionLocal, Program, ProgramDay, ProgramSet, Exercise, Session, LoggedSet


def get_programs():
    db = SessionLocal()
    programs = db.query(Program).all()
    result = [{"id": p.id, "name": p.name} for p in programs]
    db.close()
    return result


def get_exercises_for_program(program_id: int) -> list:
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
        "avg_rest": round(r.avg_rest / 60, 2),
    } for r in results])


def get_pr_history(exercise_id: int) -> pd.DataFrame:
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
    db.close()
    if not results:
        return pd.DataFrame()
    return pd.DataFrame([{
        "date"     : sess.strftime("%Y-%m-%d"),
        "weight_lb": ls.weight_lb,
        "reps"     : ls.reps,
        "set_type" : ls.set_type,
    } for ls, sess in results])