from datetime import datetime
from db import SessionLocal, Program, ProgramDay, ProgramSet, Session, LoggedSet, Exercise, get_swap_candidates


def get_programs():
    db = SessionLocal()
    programs = db.query(Program).all()
    result = [{"id": p.id, "name": p.name} for p in programs]
    db.close()
    return result


def get_weeks(program_id: int):
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


def get_days(program_id: int, week_num: int):
    db = SessionLocal()
    days = (
        db.query(ProgramDay)
        .filter(ProgramDay.program_id == program_id,
                ProgramDay.week_num == week_num)
        .order_by(ProgramDay.day_num)
        .all()
    )
    result = [{"id": d.id, "label": d.label, "day_num": d.day_num} for d in days]
    db.close()
    return result


def get_day_label(program_day_id: int) -> str:
    db = SessionLocal()
    day = db.query(ProgramDay).filter(ProgramDay.id == program_day_id).first()
    db.close()
    return day.label if day else "Unknown Day"


def get_planned_exercises(program_day_id: int) -> list:
    SET_TYPE_PRIORITY = {"warmup": 0, "working": 1, "amrap": 2, "dropset": 3}

    def normalize_set_type(notes):
        if not notes:
            return "working"
        n = notes.strip().lower().replace(" ", "")
        if n in ("warmup", "warm-up"):
            return "warmup"
        if n == "amrap":
            return "amrap"
        if n in ("dropset", "drop", "ds", "tripleds"):
            return "dropset"
        return "working"

    def get_priority(notes):
        return SET_TYPE_PRIORITY.get(normalize_set_type(notes), 1)
    db = SessionLocal()
    day = db.query(ProgramDay).filter(ProgramDay.id == program_day_id).first()
    if not day:
        db.close()
        return []

    exercises = {}
    for ps in sorted(day.sets, key=lambda x: (get_priority(x.notes), x.set_num)):
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
            "set_type"      : normalize_set_type(ps.notes),
        })
    db.close()
    return list(exercises.values())


def get_last_best_set(exercise_id: int, current_session_id: int) -> str:
    db = SessionLocal()
    last = (
        db.query(LoggedSet)
        .filter(LoggedSet.exercise_id == exercise_id,
                LoggedSet.session_id  != current_session_id,
                LoggedSet.set_type    != "warmup")
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


def log_set(session_id, exercise_id, program_set_id, set_num,
            weight_lb, reps, rir, rest_secs, set_type="working"):
    db = SessionLocal()
    is_pr = False
    if set_type in ("working", "amrap"):
        prev = (
            db.query(LoggedSet)
            .filter(LoggedSet.exercise_id == exercise_id,
                    LoggedSet.set_type.in_(["working", "amrap"]))
            .order_by(LoggedSet.weight_lb.desc())
            .first()
        )
        if prev is None:
            is_pr = False
        elif weight_lb > prev.weight_lb:
            is_pr = True
        else:
            best_reps = (
                db.query(LoggedSet)
                .filter(LoggedSet.exercise_id == exercise_id,
                        LoggedSet.weight_lb   == prev.weight_lb,
                        LoggedSet.set_type.in_(["working", "amrap"]))
                .order_by(LoggedSet.reps.desc())
                .first()
            )
            is_pr = (weight_lb == prev.weight_lb and reps > best_reps.reps)

    entry = LoggedSet(
        session_id=session_id, exercise_id=exercise_id,
        program_set_id=program_set_id, set_num=set_num,
        weight_lb=weight_lb, reps=reps, rir=rir,
        rest_secs=rest_secs, is_pr=is_pr, set_type=set_type,
        logged_at=datetime.utcnow(),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    db_id = entry.id
    db.close()
    return is_pr, db_id


def create_session(program_day_id: int) -> int:
    db = SessionLocal()
    s = Session(program_day_id=program_day_id, date=datetime.utcnow())
    db.add(s)
    db.commit()
    db.refresh(s)
    sid = s.id
    db.close()
    return sid


def get_open_session_for_day(program_day_id: int):
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    db = SessionLocal()
    session = (
        db.query(Session)
        .filter(Session.program_day_id == program_day_id,
                Session.date >= today_start,
                Session.duration_mins == None)
        .order_by(Session.date.desc())
        .first()
    )
    if session is None:
        db.close()
        return None, None
    has_sets = db.query(LoggedSet).filter(LoggedSet.session_id == session.id).count() > 0
    db.close()
    return (session.id, session.date) if has_sets else (None, None)


def rehydrate_session(session_id: int):
    db = SessionLocal()
    sets = (
        db.query(LoggedSet)
        .filter(LoggedSet.session_id == session_id)
        .order_by(LoggedSet.logged_at)
        .all()
    )
    logged_sets = {}
    adhoc_sets = {}
    adhoc_counter = -1
    last_logged_key = None
    last_logged_at = None

    for s in sets:
        if s.program_set_id is not None:
            key = str(s.program_set_id)
        else:
            key = str(adhoc_counter)
            adhoc_counter -= 1
            eid = s.exercise_id
            if eid not in adhoc_sets:
                adhoc_sets[eid] = []
            adhoc_sets[eid].append(key)

        logged_sets[key] = {
            "weight_lb": s.weight_lb,
            "reps":      s.reps,
            "rir":       s.rir,
            "rest_secs": s.rest_secs,
            "is_pr":     s.is_pr,
            "db_id":     s.id,
            "set_type":  s.set_type,
        }
        last_logged_key = key
        last_logged_at = s.logged_at

    db.close()
    return logged_sets, adhoc_sets, adhoc_counter, last_logged_key, last_logged_at


def get_next_program_day(program_id: int):
    db = SessionLocal()
    last = (
        db.query(Session, ProgramDay)
        .join(ProgramDay, ProgramDay.id == Session.program_day_id)
        .filter(ProgramDay.program_id == program_id,
                Session.duration_mins != None)
        .order_by(Session.date.desc())
        .first()
    )
    if not last:
        db.close()
        return None, None

    _, last_day = last
    current_week = last_day.week_num
    current_day  = last_day.day_num

    days_in_week = (
        db.query(ProgramDay)
        .filter(ProgramDay.program_id == program_id,
                ProgramDay.week_num == current_week)
        .order_by(ProgramDay.day_num)
        .all()
    )
    max_day = max(d.day_num for d in days_in_week)

    if current_day < max_day:
        next_week, next_day = current_week, current_day + 1
    else:
        all_weeks = [w.week_num for w in (
            db.query(ProgramDay.week_num)
            .filter(ProgramDay.program_id == program_id)
            .distinct().order_by(ProgramDay.week_num).all()
        )]
        max_week = max(all_weeks)
        if current_week < max_week:
            next_week = all_weeks[all_weeks.index(current_week) + 1]
        else:
            next_week = all_weeks[0]
        next_day = 1

    db.close()
    return next_week, next_day


def finish_session(session_id: int, session_secs: int):
    db = SessionLocal()
    s = db.query(Session).filter(Session.id == session_id).first()
    if s:
        s.duration_mins = session_secs // 60
        db.commit()
    db.close()


def undo_set(db_id: int):
    db = SessionLocal()
    entry = db.query(LoggedSet).filter(LoggedSet.id == db_id).first()
    if entry:
        db.delete(entry)
        db.commit()
    db.close()