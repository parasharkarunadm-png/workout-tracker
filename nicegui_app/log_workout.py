from nicegui import ui
from nicegui_app.state import WorkoutSession
from db import SessionLocal, Program, ProgramDay, Session, LoggedSet

PHAT_ASCII = """
#%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%%##+=++====+#@@@@@@@@@@@#------*%%%%%#+-----+@@@@@@@@@@
#%%%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@##@#*******###**#@@@@@@@@@#----=+**#%@@@#+=-:.:-#@@@@@@@@
#%%%%%%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%*%*--=#%*#%@@@@@%#%@@@@@@@@*=+##%%@@@@@@#++=-::-=+%@@@@@@
#%%%%%%%%@@%#+=--=+*#%@@@@@@@@@@%@@@@@@@@%#%#+---=*=--=+#@@@%*#@@@@@@@@@@%%%@@@@@@@%+===-::-==#@@@@@
%%%%%%%%%%+:::::::----=%@@@@@@@@%@@@@@@@@@%%+---:::---==+#@@%*#@@@@@@@@@@@@@@@@@@@@@*+==----=++#@@@@
%%%@%%%%%+----=++++=**+%@@@@@@@@@@@@@@@@@@@@+=+*+==+#######@@@@@@@@@@@@@@@@@@@@@@@@@*===-:---+++%@@@
%@@@@@@%*==++=+*=++-*+=#@@@@@@@@@@@@@@@@@@@%#%%%%+=*%%#%####@@##@@@@@@@@@@@@@@@@@@@@*===-:::-+++*@@@
%@@@@@%*==*#%+*+=*==*=+%@@@@@@@@@@@@@@@@@%@%*++--==+=-----=*%@@@@@@@@@@@@@@@@@@@@@@@#+==-::-=++++#@@
%@@@@%*==+#%#%%%%#*###%@@@@@@@@@@@@@@@@@@%@#----===++=-==++#%@@@@@@@@@@@@@@@@@@@@@@@%*+++++=-++++*%%
@@@@#=---=##%@@@@%%%%@@@@@@@@@@@@@@@@@@@@@@%+==-=*#*+===+##%%*#@@@@@@@@@@@@@@@@@@@@@%#****++++=+***#
%@%*==--=#%#%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%*+===++***++***#%@@%#@@@@@@@@@@@@@@#=:...=##**+++====-=+
@#+=---=#%%%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@#+===+++++=+**#%%%@@@@@@@@@@@@@@@#-:::::--******+==--=+#
*+=-===+#%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@#++==--==+*##%%##@@@@@@@@@@%###=----:::-=+++***+===+#%%
*==--=+*#@@%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%*+++***##%%%###%@@@@@%=:...:======-----+++===++*#%%%%
*=-=+*##%%%%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%%%%%%%%@%###*=*@@+::::::-+++++++++++++++***###%%%@@
*++***##%%%%@@@#*++#%@@@@@@@@%%%%@@@@@@@@@@@@@@@%%%%%%%@%####*=----:::-=++*******+++++**######%%%@@@
**+***#%@@@@%*=-:::.:*%@@%+-:.....:=+#@@@@@@@@@@##%@@@@@%#**+===--::-=*#*+*##**++=====++**###%%@@@@@
**####%%%#*+==--:::--:-+----::::....::-+%@@@#+:.=**%@@%*==+====--::-+*#+-=+**++=++++++++**###%@@@@@@
**+*##*++==++===------::-=+==--::::::.........-=--=+*+==+++====---=+*#*=*##***+++++++***####%@@@@@@@
####*#**+--+******+++=====++==---::::-:----:::--==-=+===++===---==+*##**#%%%###*****#######%@@@@@@@@
###*#*==--=**#######*****++++==--::---------------======+===--=++**#%%%%%%%%%%%#########*#@@@@@@@@@@
++++=++**+++*****#######*+++*+++==---------------=+=====+=====+**##%%%%%#**###%######*##@@@@@@@@@@@@
######***++=--====++***######***++==---------:---=++========+***#%%%###+++***##%%###%@@@@@@@@@@@@@@@
#%%%%%#*++++++++*****###%%%%%%#***++=====---:---=++=======++**##%%%%#*-::-=+*##%%%@@@@@@@@@@@@@@@@@@
%@@%%###*********####%%%####*####**+++===--::--=++++++==+++**#%%%%%%#+-----=+*##%@@@@@@@@@@@@@@@@@@@
%@@@@%%###########%%%%%%%%##***%%#**+++===-::--=+++++++++**##%%%%#***======++*#%%@@@@@@@@@@@@@@@@@@@
%@@@@@@@%%%##############%#***++%%#***+++==-=+++*********#%%%%%#***+====+++**##%%@@@@@@@@@@@@@@@@@@@
%@@@@@@@@%%%%%%%%%@@@@@@@@@#+++++#%##*********==+*##*###%%%%%#*+===--==++****##%%@@@@@@@@@@@@@@@@@@@
%@@@@@@@%%%%%%%%%@@@@@@@@@@@#***++*%%#####*+===+++++++++++**++=========++***###%%@@@@@@@@@@@@@@@@@@@
%@@@@@@@%%%%%%%%%@@@@@@@@@@@@#***++*###*++==---====-==+====---==++++===++**####%@@@@@@@@@@@@@@@@@@@@
%@@@@@@@%%%%%%%%%@@@@@@@@@@@@@#***++**++++++=++++++++=------==+++++++==++**###%%@@@@@@@@@@@@@@@@@@@@
%@@@@@@@%%%%%%%@@@@@@@@@@@@@@@@%**+****************+++++=--======++*+++++*####%@@@@@@@@@@@@@@@@@@@@@
%@@@@@@@@%%@@%%@@@@@@@@@@@@@@@@@%***************###****+=--====+*****+++**##%%@@@@@@@@@@@@@@@@@@@@@@
%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@#*******+++*******+==+***+=++******##***##%%@@@@@@@@@@@@@@@@@@@@@@@
%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@##*************++++++**#*++****##########%@@@@@@@@@@@@@@@@@@@@@@@%
%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@###########*********################*############*****###*#*####*
%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%*########*********##%#*###%%######**##*+++*#%@%*++++++++********
%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%++*******+*****#####*+===++**###%####*+++++**@@*+++*************
%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@#*****+====++*+++=+++==--==+++*#%%##***++++++*@@*****************
%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%==+*+++===++======+++==-===+**#%%%#***********%@#****************
"""
DORIAN_ASCII = """
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%#***%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@%%#**+++++++=+@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@%#*******+****#####*+++*@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@%*++++++==++##%%@@@@@@@%**%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@-=+==++==*%%%%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@=-====+*###+%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@*::=+#%%%%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@%::-+**=+**#%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@-:-+==++*****%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@=:-+*+#%%##*-+@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@#--=####+=+*++#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@+===*-=====+++++*@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@+-==--++=-=++*=++*@@@@@@@@@@@%@@@%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@%=--+++++***%#+*=+%@@@@@@@@@@%#@@@@%@%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@#-====#%@%==+*=-=#@@@%%@@@@@@%####%@#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@+-+++**+===+*==++*%%@@%%@@@@@@@@@%%@%#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@#==+%%#====--===----*%@#%@@@@@@@@%%%%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@=--=**=-=====++=----:**@@**#@@@@@@@%%%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@%----++-:=*+*#*+=-----++*%%@@@%@@@@@@#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@%--:=++=-=*#%%#+=++=-=+##%=*%@##%%%#*%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@+-:-*==:=#%%%+-==:-=+=+#@%%%%#%*+##@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@*=---=*##%%*--===--:-==+#@%%%%#+#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@%=+++#%%+-----====----==++*%%%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@+*++#=-:::--==========+++=#%%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@++**-::::----===*###%%#+-+=%%%%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@+++=:-==+==-::-=++*#%%%#+#%%###**@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@++=-:=+++-::::=*#%%%*====**=+=++=*@@@@@@@@@@####%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@#--:-+++=::-:=*%%%#%#==+++++=++=-=@@@@@@@@@#++==+*@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@+-:=+++-::::=+++==+*++###**+++*-+@@@@@@@@##%*++++*@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@#--=***+=--=+*****#%%%#%%%%#**#+*#%@@@@@@@@@@%#+++%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@=--+********#%%%%@@@@%#%@%%%##===+*@@@@@@@@@**#%*%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@*---+***###%%@@@#*%@%==#%#+%*=-=++=@@@@@@%+*#%@%%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@#--=-=+#%%@@@%%*--#@@+-**====++**#%@@%*+++#%%%%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@###%%%%%@@@@@@@#**%@@%==*--=+*%%###*++**++##%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@#**###%%%@@@@@@@@@%@@@@@++==+*##%#+++*##*#%%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@**###%%@@@@@@@@@@%#@@@@@@#+***%%#==*%@@@@%%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@%**##%@@@@@@@@@@@@%##@@@@@@@#*+***+#@@@@@#%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@%###%@@@@@@@@@@@@@%%#%@@@@@@@@@#+*#%@@@%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@%###%%@@@@@#=----==+**#%@@@@@@@@@@##%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@%%%%@%+============+=*#%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

"""



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
        next_week = all_weeks[all_weeks.index(current_week) + 1] if current_week < max(all_weeks) else all_weeks[0]
        next_day = 1

    db.close()
    return next_week, next_day


def get_open_session_for_day(program_day_id: int):
    from datetime import datetime
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

def screen_logger(session: WorkoutSession, day_id: int, open_sid: int = None):
    from nicegui_app.services import (
        get_planned_exercises, get_last_best_set,
        log_set, create_session, rehydrate_session, finish_session
    )
    from datetime import datetime

    # --- Init session state ---
    if open_sid:
        logged, adhoc, counter, last_key, last_at = rehydrate_session(open_sid)
        session.session_id         = open_sid
        session.logged_sets        = logged
        session.adhoc_sets         = adhoc
        session.adhoc_counter      = counter
        session.last_logged_key    = last_key
        session.last_set_time      = last_at
        session.first_set_logged   = len(logged) > 0
        session.session_start_time = datetime.utcnow()
    else:
        sid = create_session(day_id)
        session.session_id         = sid
        session.session_start_time = datetime.utcnow()

    session.program_day_id  = day_id
    session.session_started = True

    exercises = get_planned_exercises(day_id)

    # --- DB: day label ---
    db = SessionLocal()
    day = db.query(ProgramDay).filter(ProgramDay.id == day_id).first()
    day_label = day.label if day else "Workout"
    db.close()

    # --- Sticky header ---
    with ui.header().classes('w-full flex justify-between items-center px-4 py-2'):
        ui.label(day_label).classes('text-lg font-bold')
        with ui.row().classes('gap-6'):
            session_label = ui.label('Session: 00:00:00').classes('text-base font-bold')
            rest_label    = ui.label('Rest: --:--:--').classes('text-base font-bold')

    with ui.column().classes('w-full max-w-lg mx-auto p-4 gap-4'):

        # --- Timer ---
        def update_timers():
            if session.session_start_time:
                secs = int((datetime.utcnow() - session.session_start_time).total_seconds())
                h, m, s = secs // 3600, (secs % 3600) // 60, secs % 60
                session_label.set_text(f'Session: {h:02}:{m:02}:{s:02}')
            if session.last_set_time and session.first_set_logged:
                rsecs = int((datetime.utcnow() - session.last_set_time).total_seconds())
                h, m, s = rsecs // 3600, (rsecs % 3600) // 60, rsecs % 60
                rest_label.set_text(f'Rest: {h:02}:{m:02}:{s:02}')

        ui.timer(1.0, update_timers)

        # --- Exercises ---
        for ex in exercises:
            eid      = ex["exercise_id"]
            ex_name  = ex["exercise_name"]
            sets     = ex["sets"]

            effective_eid = session.exercise_swaps.get(eid, eid)
            last_best     = get_last_best_set(effective_eid, session.session_id)

            with ui.card().classes('w-full'):

                # --- Header row ---
                with ui.row().classes('w-full items-center justify-between'):
                    toggle_btn = ui.button(
                        f'▶ {ex_name} ({len(sets)} sets)',
                    ).props('flat').classes('text-left flex-1')
                    swap_btn = ui.button('🔄').props('flat round')
                logged_count = sum(1 for s in sets if str(s["program_set_id"]) in session.logged_sets)
                progress_bar = ui.linear_progress(
                    value=logged_count / len(sets) if sets else 0
                ).classes('w-full').props('color=red size=4px')
                # --- Last best (hidden until expanded) ---
                last_best_label = ui.label(last_best).classes('text-sm text-gray-400')
                last_best_label.visible = False

                # --- Expansion body (hidden until expanded) ---
                expansion_body = ui.column().classes('w-full gap-2')
                expansion_body.visible = False

                # --- Wire toggle ---
                def make_toggle(
                    body=expansion_body, lbl=last_best_label,
                    btn=toggle_btn, name=ex_name, count=len(sets)
                ):
                    def toggle():
                        body.visible = not body.visible
                        lbl.visible  = not lbl.visible
                        btn.set_text(
                            f"{'▼' if body.visible else '▶'} {name} ({count} sets)"
                        )
                    return toggle

                toggle_btn.on('click', make_toggle())

                # --- Wire swap ---
                def open_swap_dialog(
                    eid=eid, toggle_btn=toggle_btn,
                    last_best_label=last_best_label, sets=sets
                ):
                    from db import get_swap_candidates
                    candidates = get_swap_candidates(eid, day_id, session.session_id)

                    with ui.dialog() as dialog, ui.card().classes('w-full'):
                        ui.label('Swap Exercise').classes('font-bold text-lg')
                        if not candidates:
                            ui.label('No alternatives available.').classes('text-gray-400')
                            ui.button('Close', on_click=dialog.close)
                        else:
                            selected = {'id': None, 'name': None}
                            with ui.column().classes('w-full gap-2'):
                                for c in candidates:
                                    def pick(c=c):
                                        selected['id']   = c['exercise_id']
                                        selected['name'] = c['name']
                                        ui.notify(f"Selected: {c['name']}", color='positive')
                                    ui.button(
                                        f"{c['name']} ({c['equipment']})",
                                        on_click=pick
                                    ).props('flat').classes('w-full text-left')

                            def confirm_swap(
                                selected=selected, eid=eid,
                                toggle_btn=toggle_btn,
                                last_best_label=last_best_label
                            ):
                                if not selected['id']:
                                    ui.notify('Pick an exercise first', color='negative')
                                    return
                                session.exercise_swaps[eid] = selected['id']
                                new_best = get_last_best_set(selected['id'], session.session_id)
                                toggle_btn.set_text(f"▶ {selected['name']} ({len(sets)} sets)")
                                last_best_label.set_text(new_best)
                                last_best_label.visible = True
                                dialog.close()
                                ui.notify(f"Swapped to {selected['name']}", color='positive')

                            with ui.row().classes('gap-2 mt-2'):
                                ui.button('Confirm Swap', on_click=confirm_swap).props('color=blue')
                                ui.button('Cancel', on_click=dialog.close)

                    dialog.open()

                swap_btn.on('click', open_swap_dialog)
                with expansion_body:
                    # --- Set rows ---
                    set_rows = ui.column().classes('w-full gap-2')

                    def render_sets(eid=eid, sets=sets, set_rows=set_rows, progress_bar=progress_bar):
                        set_rows.clear()
                        with set_rows:
                            for s in sets:
                                psid     = str(s["program_set_id"])
                                set_type = s["set_type"]
                                set_num  = s["set_num"]
                                t_reps   = s["target_reps"]
                                t_rir    = s["target_rir"]
                                t_pct    = s["target_pct_1rm"]
                                pct_str  = f" @ {int(t_pct*100)}% 1RM" if t_pct else ""
                                rep_str  = "AMRAP" if not t_reps or set_type == "amrap" else str(t_reps)

                                if psid in session.logged_sets:
                                    logged   = session.logged_sets[psid]
                                    pr_badge = " 🏆 PR" if logged.get("is_pr") else ""
                                    rest_str = f" | Rest: {logged['rest_secs']}s" if logged.get("rest_secs") else ""
                                    ui.label(
                                        f"✅ Set {set_num} — {logged['weight_lb']}lb × {logged['reps']} reps"
                                        f" @ RIR {logged['rir']}{rest_str}{pr_badge}"
                                    ).classes('text-green-400 text-sm')
                                    continue

                                ui.label(
                                    f'Set {set_num} — Target: {rep_str} reps{pct_str}'
                                ).classes('text-sm font-bold')

                                with ui.row().classes('w-full gap-2'):
                                    w_input = ui.number(placeholder='lb',   min=0, step=0.5).classes('flex-1')
                                    r_input = ui.number(placeholder='Reps', min=0, value=t_reps).classes('flex-1')
                                    i_input = ui.number(placeholder='RIR',  min=0, value=t_rir).classes('flex-1')

                                    def handle_log(
                                        psid=psid, eid=eid, set_num=set_num,
                                        set_type=set_type,
                                        w=w_input, r=r_input, i=i_input
                                    ):
                                        effective = session.exercise_swaps.get(eid, eid)
                                        if not w.value:
                                            ui.notify('Enter weight first', color='negative')
                                            return
                                        now       = datetime.utcnow()
                                        last_ex   = session.last_set_time_by_exercise.get(effective)
                                        rest_secs = int((now - last_ex).total_seconds()) if last_ex else 0

                                        is_pr, db_id = log_set(
                                            session_id     = session.session_id,
                                            exercise_id    = effective,
                                            program_set_id = int(psid),
                                            set_num        = set_num,
                                            weight_lb      = float(w.value),
                                            reps           = int(r.value or 0),
                                            rir            = int(i.value or 0),
                                            rest_secs      = rest_secs,
                                            set_type       = set_type,
                                        )
                                        session.logged_sets[psid] = {
                                            "weight_lb": float(w.value),
                                            "reps"     : int(r.value or 0),
                                            "rir"      : int(i.value or 0),
                                            "rest_secs": rest_secs,
                                            "is_pr"    : is_pr,
                                            "db_id"    : db_id,
                                            "set_type" : set_type,
                                        }
                                        session.last_logged_key  = psid
                                        session.last_set_time    = now
                                        session.last_set_time_by_exercise[effective] = now
                                        session.first_set_logged = True
                                        render_sets(eid=eid, sets=sets, set_rows=set_rows, progress_bar=progress_bar)

                                    ui.button('Log', on_click=handle_log).props('color=red').classes('flex-1')

                        # Update progress bar
                        logged_count = sum(1 for s in sets if str(s["program_set_id"]) in session.logged_sets)
                        progress_bar.set_value(logged_count / len(sets) if sets else 0)
                    
                    render_sets()

        # --- Finish session ---
        ui.separator()

        def handle_finish():
            skipped = [
                ex["exercise_name"] for ex in exercises
                if not any(str(s["program_set_id"]) in session.logged_sets for s in ex["sets"])
                and not any(k in session.logged_sets for k in session.adhoc_sets.get(ex["exercise_id"], []))
            ]
            if skipped:
                with ui.dialog() as dialog, ui.card():
                    ui.label('⚠️ Skipped exercises:').classes('font-bold')
                    for name in skipped:
                        ui.label(f'• {name}')
                    with ui.row():
                        ui.button('Finish Anyway', on_click=lambda: (dialog.close(), do_finish())).props('color=blue')
                        ui.button('Go Back', on_click=dialog.close)
                dialog.open()
            else:
                do_finish()

        def do_finish():
            secs = int((datetime.utcnow() - session.session_start_time).total_seconds())
            finish_session(session.session_id, secs)
            ui.navigate.to('/')

        ui.button('Finish Session', on_click=handle_finish).classes('w-full').props('color=blue')


def render(session: WorkoutSession):
    programs = get_programs()
    if not programs:
        ui.label('No programs found. Go to Admin to import one.')
        return

    program_map = {p["name"]: p["id"] for p in programs}

    
    program_ascii = {
        'PHAT': PHAT_ASCII,
        'Strength by Dorian': DORIAN_ASCII,
    }

    with ui.column().classes('w-full max-w-lg mx-auto p-4 gap-4'):
        ui.label('SELECT YOUR BATTLE').classes('text-3xl font-bold tracking-widest')

        from nicegui_app.services import get_last_used_program_id
        last_pid = get_last_used_program_id()
        last_program_name = next(
            (p["name"] for p in programs if p["id"] == last_pid),
            list(program_map.keys())[0]
        )

        program_select = ui.select(
            list(program_map.keys()),
            value=last_program_name,
            label='Program',
        ).classes('w-full')

        week_select = ui.select([], label='Week').classes('w-full')
        day_select  = ui.select([], label='Day').classes('w-full')

        suggestion_label = ui.label('').classes('text-sm text-gray-400')
        ui.separator()

        action_area = ui.column().classes('w-full gap-2')

        def refresh_days():
            program_id = program_map[program_select.value]
            week_num   = int(week_select.value.replace('Week ', ''))
            days       = get_days(program_id, week_num)
            day_map    = {d["label"]: d["id"] for d in days}
            day_select.options = list(day_map.keys())
            day_select.value   = day_select.options[0] if day_select.options else None
            day_select.update()
            refresh_actions()

        def refresh_weeks():
            program_id = program_map[program_select.value]
            weeks      = get_weeks(program_id)
            sugg_week, sugg_day = get_next_program_day(program_id)
            week_select.options = [f'Week {w}' for w in weeks]
            week_select.value   = (
                f'Week {sugg_week}'
                if sugg_week and f'Week {sugg_week}' in week_select.options
                else week_select.options[0] if week_select.options else None
            )
            week_select.update()
            suggestion_label.set_text('💡 Suggested based on your last session' if sugg_week else '')
            refresh_days()

        def refresh_actions():
            action_area.clear()
            program_id = program_map[program_select.value]
            week_num   = int(week_select.value.replace('Week ', ''))
            days       = get_days(program_id, week_num)
            day_map    = {d["label"]: d["id"] for d in days}
            day_id     = day_map.get(day_select.value)
            if not day_id:
                return
            open_sid, open_date = get_open_session_for_day(day_id)
            with action_area:
                if open_sid:
                    ui.label('⚠️ An open session exists for today. Resume it?').classes('text-yellow-400')
                    with ui.row().classes('w-full gap-2'):
                        ui.button('Resume Session',
                            on_click=lambda: ui.navigate.to(f'/logger/{day_id}/{open_sid}')
                        ).classes('flex-1').props('color=blue')
                        ui.button('Start Fresh',
                            on_click=lambda: ui.navigate.to(f'/logger/{day_id}/0')
                        ).classes('flex-1').props('outline')
                else:
                    ui.button('START SESSION',
                        on_click=lambda: ui.navigate.to(f'/logger/{day_id}/0')
                    ).classes('w-full text-lg tracking-widest').props('color=red')

        # --- ASCII art ---
        ascii_display = ui.html('', sanitize=False)
        ascii_display.style(
            'font-family: monospace; font-size: 9px; line-height: 1.1; '
            'color: #aa4444; white-space: pre; overflow: hidden; '
            'width: 100%; margin-top: 16px; '
            'background: rgba(255,255,255,0.03); padding: 8px;'
        )

        def update_ascii():
            art = program_ascii.get(program_select.value, '')
            ascii_display.set_content(f'<pre>{art}</pre>')

        program_select.on('update:model-value', lambda e: (refresh_weeks(), update_ascii()))
        week_select.on('update:model-value', lambda e: refresh_days())
        day_select.on('update:model-value', lambda e: refresh_actions())

        program_select.value = last_program_name
        refresh_weeks()
        update_ascii()