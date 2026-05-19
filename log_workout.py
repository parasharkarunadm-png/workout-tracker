import streamlit as st
from datetime import datetime
from db import SessionLocal, Program, ProgramDay, Session, LoggedSet,get_swap_candidates,Exercise


# ---------------------------------------------------------------------------
# Helpers — formatting
# ---------------------------------------------------------------------------
def fmt_duration(seconds: int) -> str:
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02}:{m:02}:{s:02}"


def normalize_set_type(notes: str) -> str:
    """Normalize notes field to a consistent set_type string."""
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


SET_TYPE_PRIORITY = {
    "warmup": 0,
    "working": 1,
    "amrap": 2,
    "dropset": 3,
}


def get_set_type_priority(notes: str) -> int:
    """Return sort priority for a set type."""
    return SET_TYPE_PRIORITY.get(normalize_set_type(notes), 1)


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
    for ps in sorted(day.sets, key=lambda x: (get_set_type_priority(x.notes), x.set_num)):
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


# ---------------------------------------------------------------------------
# DB write
# ---------------------------------------------------------------------------
def log_set(session_id, exercise_id, program_set_id, set_num,
            weight_lb, reps, rir, rest_secs, set_type="working"):
    """Write one logged set. Returns (is_pr, db_id)."""
    db = SessionLocal()

    # PR only applies to working and amrap sets
    is_pr = False
    if set_type in ("working", "amrap"):
        prev_best_weight = (
            db.query(LoggedSet)
            .filter(LoggedSet.exercise_id == exercise_id,
                    LoggedSet.set_type.in_(["working", "amrap"]))
            .order_by(LoggedSet.weight_lb.desc())
            .first()
        )

        if prev_best_weight is None:
            is_pr = True
        elif weight_lb > prev_best_weight.weight_lb:
            is_pr = True
        else:
            best_reps_at_top = (
                db.query(LoggedSet)
                .filter(LoggedSet.exercise_id == exercise_id,
                        LoggedSet.weight_lb   == prev_best_weight.weight_lb,
                        LoggedSet.set_type.in_(["working", "amrap"]))
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
        set_type       = set_type,
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
def handle_log(key, exercise_id, program_set_id, set_num,
               weight, reps, rir, set_type="working"):
    now = datetime.utcnow()

    # Per-exercise rest: only counts time since last set of THIS exercise
    per_ex = st.session_state.get("last_set_time_by_exercise", {})
    last_ex_time = per_ex.get(exercise_id)
    rest_secs = int((now - last_ex_time).total_seconds()) if last_ex_time else 0

    is_pr, db_id = log_set(
        session_id     = st.session_state.session_id,
        exercise_id    = exercise_id,
        program_set_id = program_set_id,
        set_num        = set_num,
        weight_lb      = weight,
        reps           = reps,
        rir            = rir if rir is not None else 0,
        rest_secs      = rest_secs,
        set_type       = set_type,
    )

    st.session_state.logged_sets[key] = {
        "weight_lb": weight,
        "reps"     : reps,
        "rir"      : rir if rir is not None else 0,
        "rest_secs": rest_secs,
        "is_pr"    : is_pr,
        "db_id"    : db_id,
        "set_type" : set_type,
    }

    # Update both global (for header display) and per-exercise (for rest calc)
    st.session_state.last_logged_key  = key
    st.session_state.last_set_time    = now
    st.session_state.first_set_logged = True
    if "last_set_time_by_exercise" not in st.session_state:
        st.session_state.last_set_time_by_exercise = {}
    st.session_state.last_set_time_by_exercise[exercise_id] = now

# ---------------------------------------------------------------------------
# Set label helper
# ---------------------------------------------------------------------------
def get_set_label(sets: list, current_index: int) -> str:
    """Generate display label like W1, W2, 1, 2, D1 based on set type."""
    s        = sets[current_index]
    set_type = s.get("set_type", "working")
    count    = sum(
        1 for x in sets[:current_index + 1]
        if x.get("set_type") == set_type
    )
    if set_type == "warmup":
        return f"W{count}"
    if set_type == "dropset":
        return f"D{count}"
    return str(count)  # working and amrap share numbering


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

def get_open_session_for_day(program_day_id: int):
    from datetime import date
    db = SessionLocal()
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    session = (
        db.query(Session)
        .filter(
            Session.program_day_id == program_day_id,
            Session.date >= today_start,
            Session.duration_mins == None
        )
        .order_by(Session.date.desc())
        .first()
    )
    if session is None:
        db.close()
        return None, None

    # Only resumable if sets were actually logged
    has_sets = db.query(LoggedSet).filter(LoggedSet.session_id == session.id).count() > 0
    db.close()

    if not has_sets:
        return None, None

    return session.id, session.date


def rehydrate_session(session_id: int, program_day_id: int, session_date: datetime):
    """Rebuild session state from DB logged_sets for a resumed session."""
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
            key = s.program_set_id
        else:
            key = adhoc_counter
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

    st.session_state.session_id         = session_id
    st.session_state.program_day_id     = program_day_id
    st.session_state.session_started    = True
    st.session_state.session_start_time = session_date
    st.session_state.logged_sets        = logged_sets
    st.session_state.adhoc_sets         = adhoc_sets
    st.session_state.adhoc_counter      = adhoc_counter
    st.session_state.last_logged_key    = last_logged_key
    st.session_state.last_set_time      = last_logged_at
    st.session_state.first_set_logged   = len(logged_sets) > 0


# ---------------------------------------------------------------------------
# Screen 1 — Program day selector
# ---------------------------------------------------------------------------
def screen_select_day():
    st.subheader("Select Today's Workout")
    programs = get_programs()

    if not programs:
        st.warning("No programs found. Go to Admin to import one first.")
        return

    program_map           = {p.name: p.id for p in programs}
    selected_program_name = st.selectbox("Program", list(program_map.keys()))
    selected_program_id   = program_map[selected_program_name]

    weeks = get_weeks(selected_program_id)
    if not weeks:
        st.warning("This program has no weeks defined yet.")
        return

    # --- Smart default ---
    suggested_week, suggested_day = get_next_program_day(selected_program_id)

    week_index = (
        weeks.index(suggested_week)
        if suggested_week in weeks else 0
    )
    selected_week = st.selectbox(
        "Week", weeks,
        index=week_index,
        format_func=lambda w: f"Week {w}"
    )

    days = get_days(selected_program_id, selected_week)
    if not days:
        st.warning("No days found for this week.")
        return

    day_map    = {d.label: d.id for d in days}
    day_labels = list(day_map.keys())
    day_nums   = [d.day_num for d in days]

    day_index = (
        day_nums.index(suggested_day)
        if suggested_day in day_nums and selected_week == suggested_week else 0
    )
    selected_day_label = st.selectbox("Day", day_labels, index=day_index)
    selected_day_id    = day_map[selected_day_label]

    if suggested_week and suggested_day:
        st.caption(f"💡 Suggested based on your last session")

    st.divider()

    open_session_id, open_session_date = get_open_session_for_day(selected_day_id)

    if open_session_id:
        st.info("⚠️ An open session exists for this day from today. Resume it?")
        col1, col2 = st.columns(2)
        if col1.button("Resume Session", type="primary", use_container_width=True):
            rehydrate_session(open_session_id, selected_day_id, open_session_date)
            st.rerun()
        if col2.button("Start Fresh", use_container_width=True):
            session_id = create_session(selected_day_id)
            st.session_state.session_id         = session_id
            st.session_state.program_day_id     = selected_day_id
            st.session_state.session_started    = True
            st.session_state.last_set_time      = None
            st.session_state.session_start_time = datetime.utcnow()
            st.session_state.first_set_logged   = False
            st.rerun()
    else:
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
# Get next program day helper
# ---------------------------------------------------------------------------

def get_next_program_day(program_id: int):
    """Return (week_num, day_num) of the next suggested day based on last completed session."""
    db = SessionLocal()

    # Find last completed session for this program
    last = (
        db.query(Session, ProgramDay)
        .join(ProgramDay, ProgramDay.id == Session.program_day_id)
        .filter(
            ProgramDay.program_id  == program_id,
            Session.duration_mins  != None,
        )
        .order_by(Session.date.desc())
        .first()
    )

    if not last:
        db.close()
        return None, None

    _, last_day = last
    current_week = last_day.week_num
    current_day  = last_day.day_num

    # Get all days in current week
    days_in_week = (
        db.query(ProgramDay)
        .filter(
            ProgramDay.program_id == program_id,
            ProgramDay.week_num   == current_week,
        )
        .order_by(ProgramDay.day_num)
        .all()
    )
    max_day = max(d.day_num for d in days_in_week)

    if current_day < max_day:
        # Next day in same week
        next_week = current_week
        next_day  = current_day + 1
    else:
        # End of week — move to next week day 1
        all_weeks = (
            db.query(ProgramDay.week_num)
            .filter(ProgramDay.program_id == program_id)
            .distinct()
            .order_by(ProgramDay.week_num)
            .all()
        )
        week_nums = [w.week_num for w in all_weeks]
        max_week  = max(week_nums)

        if current_week < max_week:
            next_week = week_nums[week_nums.index(current_week) + 1]
        else:
            next_week = week_nums[0]  # wrap to first week

        next_day = 1

    db.close()
    return next_week, next_day


# ---------------------------------------------------------------------------
# Screen 2 — Logger
# ---------------------------------------------------------------------------
def screen_logger():
    now = datetime.utcnow()

    session_start    = st.session_state.get("session_start_time")
    last_set_time    = st.session_state.get("last_set_time")
    first_set_logged = st.session_state.get("first_set_logged", False)

    session_secs  = int((now - session_start).total_seconds()) if session_start else 0
    rest_secs_hdr = int((now - last_set_time).total_seconds()) if (last_set_time and first_set_logged) else 0

    day_label = get_day_label(st.session_state.program_day_id)

    # --- Header — timers ---
    st.markdown(f"### {day_label}")
    col1, col2 = st.columns(2)
    col1.metric("Session", fmt_duration(session_secs))
    col2.metric("Rest", fmt_duration(rest_secs_hdr) if first_set_logged else "--:--:--")
    st.divider()

    # --- Exercises ---
    exercises = get_planned_exercises(st.session_state.program_day_id)
    if not exercises:
        st.warning("No exercises found for this program day.")
        return

    for ex in exercises:
        eid = ex["exercise_id"]

        # --- Resolve swap ---
        swapped_id = st.session_state.get("exercise_swaps", {}).get(eid)
        if swapped_id:
            db = SessionLocal()
            swapped_ex = db.query(Exercise).filter(Exercise.id == swapped_id).first()
            db.close()
        else:
            swapped_ex = None

        effective_eid = swapped_id if swapped_id else eid
        display_name  = swapped_ex.name if swapped_ex else ex["exercise_name"]
        total_sets    = len(ex["sets"])
        last_best     = get_last_best_set(effective_eid, st.session_state.session_id)

        # --- Exercise header row: name + swap button ---
        col_name, col_swap = st.columns([5, 1])
        col_name.markdown(f"#### {display_name} ({total_sets} sets)")

        with col_swap.popover("🔄"):
            try:
                candidates = get_swap_candidates(eid, st.session_state.program_day_id)
                if not candidates:
                    st.caption("No alternatives available.")
                else:
                    options = {f"{c['name']} ({c['equipment']})": c["exercise_id"] for c in candidates}
                    selected_label = st.radio("Swap to:", list(options.keys()), key=f"swap_radio_{eid}")
                    if st.button("Confirm Swap", key=f"swap_confirm_{eid}"):
                        if "exercise_swaps" not in st.session_state:
                            st.session_state.exercise_swaps = {}
                        st.session_state.exercise_swaps[eid] = options[selected_label]
                        st.rerun()
            except Exception as e:
                st.error(f"Swap unavailable: {e}")

        # --- Expander for sets ---
        logged_count = sum(
            1 for s in ex["sets"]
            if s["program_set_id"] in st.session_state.logged_sets
        )
        expander_label = f"{last_best} — {logged_count}/{total_sets} logged"

        is_open = eid in st.session_state.get("expanded_exercises", set())
        if st.button(f"{'▼' if is_open else '▶'} {expander_label}", key=f"expand_{eid}", use_container_width=True):
            expanded = st.session_state.get("expanded_exercises", set())
            if eid in expanded:
                expanded.discard(eid)
            else:
                expanded.add(eid)
            st.session_state.expanded_exercises = expanded
            st.rerun()

        if is_open:
            if swapped_ex:
                st.caption(f"🔄 Swapped from {ex['exercise_name']}")

            # Planned sets
            for idx, s in enumerate(ex["sets"]):
                psid      = s["program_set_id"]
                set_type  = s.get("set_type", "working")
                set_label = get_set_label(ex["sets"], idx)
                rep_label = "AMRAP" if (s["target_reps"] is None or set_type == "amrap") else str(s["target_reps"])
                pct_label = f" @ {int(s['target_pct_1rm']*100)}% 1RM" if s["target_pct_1rm"] else ""
                type_tag  = f" `{set_type}`" if set_type != "working" else ""

                if psid in st.session_state.logged_sets:
                    logged   = st.session_state.logged_sets[psid]
                    pr_badge = " 🏆 PR" if logged.get("is_pr") else ""
                    rest_str = f" | Rest: {fmt_duration(logged['rest_secs'])}" if logged["rest_secs"] else ""
                    st.success(f"✅ Set {set_label}{type_tag} — {logged['weight_lb']}lb × {logged['reps']} reps @ RIR {logged['rir']}{rest_str}{pr_badge}")
                    continue

                st.markdown(f"**Set {set_label}**{type_tag} — Target: {rep_label} reps{pct_label}")
                c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
                weight = c1.number_input("lb",   min_value=0.0, step=0.5, value=None, placeholder="lb",   key=f"weight_{psid}", label_visibility="collapsed")
                reps   = c2.number_input("Reps", min_value=0,   value=s["target_reps"] if s["target_reps"] else None, placeholder="Reps", key=f"reps_{psid}", label_visibility="collapsed")
                rir    = c3.number_input("RIR",  min_value=0,   value=s["target_rir"]  if s["target_rir"]  else None, placeholder="RIR",  key=f"rir_{psid}",  label_visibility="collapsed")

                if c4.button("Log", key=f"log_{psid}"):
                    if weight is None:
                        st.warning("Enter weight before logging.")
                        st.stop()
                    try:
                        handle_log(psid, effective_eid, psid, s["set_num"], weight, reps, rir, set_type)
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
                    c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
                    weight = c1.number_input("lb",   min_value=0.0, step=0.5, value=None, placeholder="lb",   key=f"weight_{akey}", label_visibility="collapsed")
                    reps   = c2.number_input("Reps", min_value=0,              value=None, placeholder="Reps", key=f"reps_{akey}", label_visibility="collapsed")
                    rir    = c3.number_input("RIR",  min_value=0,              value=None, placeholder="RIR",  key=f"rir_{akey}",  label_visibility="collapsed")

                    if c4.button("Log", key=f"log_{akey}"):
                        if weight is None:
                            st.warning("Enter weight before logging.")
                            st.stop()
                        try:
                            handle_log(akey, effective_eid, None, adhoc_set_num, weight, reps, rir, "working")
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

    # --- Bottom actions ---
    st.divider()
    if st.session_state.last_logged_key is not None:
        if st.button("↩️ Undo Last Set", use_container_width=True):
            undo_last_set()
            st.rerun()

    if st.button("Finish Session", type="primary", use_container_width=True):
        db = SessionLocal()
        s = db.query(Session).filter(Session.id == st.session_state.session_id).first()
        if s:
            s.duration_mins = session_secs // 60
            db.commit()
        db.close()

        sets       = list(st.session_state.logged_sets.values())
        total_sets = len(sets)
        total_prs  = sum(1 for s in sets if s.get("is_pr"))
        rest_times = [s["rest_secs"] for s in sets if s.get("rest_secs")]
        total_rest = sum(rest_times)
        avg_rest   = int(total_rest / len(rest_times)) if rest_times else 0

        st.session_state.summary_data = {
            "duration_secs": session_secs,
            "total_sets"   : total_sets,
            "total_prs"    : total_prs,
            "total_rest"   : total_rest,
            "avg_rest"     : avg_rest,
            "day_label"    : day_label,
        }

        for key, val in {
            "session_started"          : False,
            "session_id"               : None,
            "program_day_id"           : None,
            "last_set_time"            : None,
            "last_set_time_by_exercise": {},
            "session_start_time"       : None,
            "first_set_logged"         : False,
            "logged_sets"              : {},
            "adhoc_sets"               : {},
            "adhoc_counter"            : -1,
            "last_logged_key"          : None,
            "exercise_swaps"           : {},
            "expanded_exercises": set(),
        }.items():
            st.session_state[key] = val

        st.session_state.show_summary = True
        st.rerun()


# ---------------------------------------------------------------------------
# Session summary screen
# ---------------------------------------------------------------------------
def screen_summary():
    d = st.session_state.summary_data

    st.markdown(f"## ✅ Session Complete")
    st.markdown(f"### {d['day_label']}")
    st.divider()

    col1, col2 = st.columns(2)
    col1.metric("Duration",    fmt_duration(d["duration_secs"]))
    col2.metric("Sets Logged", d["total_sets"])

    col3, col4 = st.columns(2)
    col3.metric("Total Rest",  fmt_duration(d["total_rest"]))
    col4.metric("Avg Rest",    fmt_duration(d["avg_rest"]))

    if d["total_prs"] > 0:
        st.success(f"🏆 {d['total_prs']} PR{'s' if d['total_prs'] > 1 else ''} this session!")
    else:
        st.info("No PRs this session — keep grinding.")

    st.divider()

    if st.button("Back to Home", type="primary", use_container_width=True):
        st.session_state.show_summary = False
        st.session_state.summary_data = None
        st.rerun()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def render():
    if st.session_state.show_summary:
        screen_summary()
    elif not st.session_state.session_started:
        screen_select_day()
    else:
        screen_logger()