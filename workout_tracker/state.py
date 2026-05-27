import asyncio
import reflex as rx
from datetime import datetime
from typing import Any


class SetRowState(rx.ComponentState):
    """Local state for individual set row component."""
    set_info: str = ""
    weight: str = ""
    reps: str = ""
    rir: str = ""
    
    def set_weight(self, value: str):
        self.weight = value
    
    def set_reps(self, value: str):
        self.reps = value
    
    def set_rir(self, value: str):
        self.rir = value


class WorkoutState(rx.State):
    # --- Session state ---
    session_started: bool = False
    session_id: int = 0
    program_day_id: int = 0
    session_start_time: str = ""
    last_set_time: str = ""
    first_set_logged: bool = False
    finish_requested: bool = False
    show_summary: bool = False
    last_best: str = ""

    # --- Logged data ---
    logged_sets: dict[str, Any] = {}
    adhoc_sets: dict[str, list] = {}
    adhoc_counter: int = -1
    last_logged_key: str = ""
    last_set_time_by_exercise: dict[str, str] = {}
    exercise_swaps: dict[str, int] = {}
    expanded_exercises: list[int] = []
    expanded_exercise_sets: list[str] = []
    expanded_index: int = -1
    expanded_header: str = ""
    input_values: dict[str, dict] = {}

    # --- Summary ---
    summary_data: dict[str, Any] = {}

    # --- Screen 1 dropdowns ---
    programs: list[dict] = []
    selected_program_id: int = 0
    selected_program_name: str = ""
    weeks: list[str] = []
    selected_week: str = ""
    days: list[dict] = []
    selected_day_id: int = 0
    selected_day_label: str = ""
    suggested_week: int = 0
    suggested_day: int = 0
    open_session_id: int = 0
    open_session_date: str = ""
    has_open_session: bool = False

    # --- Timers ---
    session_secs: int = 0
    rest_secs: int = 0

    # --- Exercises ---
    exercises: list[dict] = []

    # -----------------------------------------------------------------------
    # Screen 1
    # -----------------------------------------------------------------------
    def load_programs(self):
        from workout_tracker.services.workout_service import get_programs
        self.programs = get_programs()
        if self.programs:
            self.selected_program_id   = self.programs[0]["id"]
            self.selected_program_name = self.programs[0]["name"]
            self.load_weeks()

    def on_program_change(self, name: str):
        self.selected_program_name = name
        match = next((p for p in self.programs if p["name"] == name), None)
        if match:
            self.selected_program_id = match["id"]
            self.load_weeks()

    def load_weeks(self):
        from workout_tracker.services.workout_service import get_weeks, get_next_program_day
        self.weeks = [str(w) for w in get_weeks(self.selected_program_id)]
        week, day = get_next_program_day(self.selected_program_id)
        self.suggested_week = week or 0
        self.suggested_day  = day or 0
        self.selected_week  = (
            str(self.suggested_week)
            if str(self.suggested_week) in self.weeks
            else (self.weeks[0] if self.weeks else "")
        )
        self.load_days()

    def on_week_change(self, week: str):
        self.selected_week = week
        self.load_days()

    def load_days(self):
        from workout_tracker.services.workout_service import get_days
        self.days = get_days(self.selected_program_id, int(self.selected_week))
        if not self.days:
            return
        match = next(
            (d for d in self.days
             if d["day_num"] == self.suggested_day
             and self.selected_week == str(self.suggested_week)),
            None
        )
        self.selected_day_id    = match["id"]    if match else self.days[0]["id"]
        self.selected_day_label = match["label"] if match else self.days[0]["label"]
        self.check_open_session()

    def on_day_change(self, label: str):
        match = next((d for d in self.days if d["label"] == label), None)
        if match:
            self.selected_day_id    = match["id"]
            self.selected_day_label = match["label"]
            self.check_open_session()

    def check_open_session(self):
        from workout_tracker.services.workout_service import get_open_session_for_day
        sid, sdate = get_open_session_for_day(self.selected_day_id)
        if sid:
            self.has_open_session  = True
            self.open_session_id   = sid
            self.open_session_date = str(sdate)
        else:
            self.has_open_session  = False
            self.open_session_id   = 0
            self.open_session_date = ""

    # -----------------------------------------------------------------------
    # Session init
    # -----------------------------------------------------------------------
    async def start_session(self):
        from workout_tracker.services.workout_service import create_session
        sid = create_session(self.selected_day_id)
        self._init_session(sid, self.selected_day_id, datetime.utcnow().isoformat())
        return WorkoutState.start_timer()

    async def resume_session(self):
        from workout_tracker.services.workout_service import rehydrate_session
        logged, adhoc, counter, last_key, last_at = rehydrate_session(self.open_session_id)
        self._init_session(self.open_session_id, self.selected_day_id, self.open_session_date)
        self.logged_sets      = logged
        self.adhoc_sets       = adhoc
        self.adhoc_counter    = counter
        self.last_logged_key  = last_key or ""
        self.last_set_time    = last_at.isoformat() if last_at else ""
        self.first_set_logged = len(logged) > 0
        return WorkoutState.start_timer()

    def _init_session(self, sid: int, day_id: int, start_time: str):
        self.session_id         = sid
        self.program_day_id     = day_id
        self.session_started    = True
        self.session_start_time = start_time
        self.last_set_time      = ""
        self.first_set_logged   = False
        self.logged_sets        = {}
        self.adhoc_sets         = {}
        self.adhoc_counter      = -1
        self.last_logged_key    = ""
        self.exercise_swaps     = {}
        self.expanded_exercises = []
        self.finish_requested   = False
        self.input_values       = {}
        self.load_exercises()

    # -----------------------------------------------------------------------
    # Background timer
    # -----------------------------------------------------------------------
    @rx.event(background=True)
    async def start_timer(self):
        import asyncio
        while True:
            await asyncio.sleep(1)
            async with self:
                if not self.session_started:
                    break
                if self.session_start_time:
                    start = datetime.fromisoformat(self.session_start_time)
                    self.session_secs = int((datetime.utcnow() - start).total_seconds())
                if self.last_set_time and self.first_set_logged:
                    last = datetime.fromisoformat(self.last_set_time)
                    self.rest_secs = int((datetime.utcnow() - last).total_seconds())
    @rx.var
    def session_time_display(self) -> str:
        h = self.session_secs // 3600
        m = (self.session_secs % 3600) // 60
        s = self.session_secs % 60
        return f"{h:02}:{m:02}:{s:02}"

    @rx.var
    def rest_time_display(self) -> str:
        h = self.rest_secs // 3600
        m = (self.rest_secs % 3600) // 60
        s = self.rest_secs % 60
        return f"{h:02}:{m:02}:{s:02}"
    # -----------------------------------------------------------------------
    # Screen 2
    # -----------------------------------------------------------------------
    @rx.var
    def get_set_strings_for_exercise(self) -> dict[int, list[str]]:
        result = {}
        for ex in self.exercises:
            eid = ex.get("exercise_id", 0)
            strings = []
            for s in ex.get("sets", []):
                strings.append(
                    f"{s.get('program_set_id')}|"
                    f"{s.get('set_num')}|"
                    f"{s.get('target_reps')}|"
                    f"{s.get('target_rir')}|"
                    f"{s.get('target_pct_1rm')}|"
                    f"{s.get('set_type')}|"
                    f"{eid}"
                )
            result[eid] = strings
        return result
    
    @rx.var
    def total_sets_summary(self) -> int:
        return self.summary_data.get("total_sets", 0)

    @rx.var
    def total_prs_summary(self) -> int:
        return self.summary_data.get("total_prs", 0)

    @rx.var
    def duration_summary(self) -> int:
        return self.summary_data.get("duration_secs", 0)

    @rx.var
    def day_label_summary(self) -> str:
        return self.summary_data.get("day_label", "")
    
    @rx.var
    def exercise_names(self) -> list[str]:
        return [str(ex.get("exercise_name", "")) for ex in self.exercises]

    @rx.var
    def exercise_ids(self) -> list[int]:
        return [int(ex.get("exercise_id", 0)) for ex in self.exercises]

    @rx.var
    def exercise_set_counts(self) -> list[int]:
        return [int(len(ex.get("sets", []))) for ex in self.exercises]
    
    @rx.var
    def exercise_display_headers(self) -> list[str]:
        return [
            f"{i}||{ex.get('exercise_name')} ({len(ex.get('sets', []))} sets)"
            for i, ex in enumerate(self.exercises)
        ]
    
    @rx.var
    def get_psid_from_set_string(self) -> dict[str, str]:
        """Map encoded set string -> psid for UI lookup."""
        result = {}
        for s in self.expanded_exercise_sets:
            parts = s.split("|")
            result[s] = parts[0]
        return result

    @rx.var
    def expanded_set_labels_map(self) -> dict[str, str]:
        """Map encoded set string -> display label for expanded sets."""
        result = {}
        for s in self.expanded_exercise_sets:
            parts = s.split("|")
            reps = parts[2] if parts[2] != "None" else "AMRAP"
            pct = f" @ {int(float(parts[4]) * 100)}% 1RM" if parts[4] not in ("None", "0.0") else ""
            result[s] = f"Set {parts[1]} — Target: {reps} reps{pct}"
        return result
    
    @rx.var
    def expanded_psids_map(self) -> dict[str, str]:
        """Map encoded set string -> program_set_id for lookup."""
        result = {}
        for s in self.expanded_exercise_sets:
            psid = s.split("|")[0]
            result[s] = psid
        return result

    @rx.var
    def exercise_headers(self) -> list[str]:
        """Encode exercise header as 'index||name||set_count' for foreach rendering."""
        return [
            f"{i}||{ex.get('exercise_name')}||{len(ex.get('sets', []))}"
            for i, ex in enumerate(self.exercises)
        ]
    
    @rx.var
    def exercise_display_labels(self) -> dict[str, str]:
        """Map encoded headers to display labels."""
        result = {}
        for header in self.exercise_headers:
            parts = header.split("||")
            if len(parts) >= 3:
                name = parts[1]
                count = parts[2]
                result[header] = f"{name} — {count} sets"
        return result
    
    @rx.var
    def exercise_logged_counts(self) -> list[int]:
        counts = []
        for ex in self.exercises:
            count = sum(
                1 for s in ex.get("sets", [])
                if str(s.get("program_set_id")) in self.logged_sets
            )
            counts.append(count)
        return counts


    def load_exercises(self):
        from workout_tracker.services.workout_service import get_planned_exercises
        self.exercises = get_planned_exercises(self.program_day_id)

    def load_last_best(self, exercise_id: int):
        from workout_tracker.services.workout_service import get_last_best_set
        self.last_best = get_last_best_set(exercise_id, self.session_id)

    def toggle_exercise_by_header(self, header: str):
        if self.expanded_header == header:
            self.expanded_header = ""
            self.expanded_index = -1
            self.expanded_exercise_sets = []
            self.last_best = ""
        else:
            self.expanded_header = header
            parts = header.split("||")
            if len(parts) >= 3:
                try:
                    idx = int(parts[0])
                    self.expanded_index = idx
                    if idx < len(self.exercises):
                        ex = self.exercises[idx]
                        eid = ex.get("exercise_id", 0)
                        self._load_set_strings(eid)
                        self.load_last_best(eid)
                except (ValueError, IndexError):
                    pass


    def _load_set_strings(self, eid: int):
        for ex in self.exercises:
            if ex.get("exercise_id") == eid:
                self.expanded_exercise_sets = [
                    f"{s.get('program_set_id')}|"
                    f"{s.get('set_num')}|"
                    f"{s.get('target_reps')}|"
                    f"{s.get('target_rir')}|"
                    f"{s.get('target_pct_1rm')}|"
                    f"{s.get('set_type')}|"
                    f"{eid}"
                    for s in ex.get("sets", [])
                ]
                break

    def update_input(self, key: str, field: str, value: str):
        if key not in self.input_values:
            self.input_values[key] = {}
        self.input_values[key][field] = value
    
    def handle_swap(self, header: str):
        """Placeholder for swap handler - to be implemented."""
        pass

    def log_set_handler(self, key: str, exercise_id: int, program_set_id: int,
                        set_num: int, set_type: str):
        from workout_tracker.services.workout_service import log_set

        vals   = self.input_values.get(key, {})
        weight = float(vals.get("weight", 0) or 0)
        reps   = int(vals.get("reps", 0) or 0)
        rir    = int(vals.get("rir", 0) or 0)

        if weight == 0:
            return

        now     = datetime.utcnow()
        last_ex = self.last_set_time_by_exercise.get(str(exercise_id))
        rest_secs = (
            int((now - datetime.fromisoformat(last_ex)).total_seconds())
            if last_ex else 0
        )

        is_pr, db_id = log_set(
            session_id     = self.session_id,
            exercise_id    = exercise_id,
            program_set_id = program_set_id if program_set_id > 0 else None,
            set_num        = set_num,
            weight_lb      = weight,
            reps           = reps,
            rir            = rir,
            rest_secs      = rest_secs,
            set_type       = set_type,
        )

        self.logged_sets[key] = {
            "weight_lb": weight,
            "reps"     : reps,
            "rir"      : rir,
            "rest_secs": rest_secs,
            "is_pr"    : is_pr,
            "db_id"    : db_id,
            "set_type" : set_type,
        }
        self.last_logged_key  = key
        self.last_set_time    = now.isoformat()
        self.first_set_logged = True
        self.last_set_time_by_exercise[str(exercise_id)] = now.isoformat()

    def undo_handler(self):
        if not self.last_logged_key:
            return
        from workout_tracker.services.workout_service import undo_set
        logged = self.logged_sets.pop(self.last_logged_key, None)
        if logged and logged.get("db_id"):
            undo_set(logged["db_id"])
        self.last_logged_key  = ""
        self.first_set_logged = len(self.logged_sets) > 0
        self.last_set_time    = ""
    def log_set_from_string(self, set_info: str):
        """Log a set from encoded string format."""
        try:
            parts = set_info.split("|")
            if len(parts) < 7:
                return
            psid = parts[0]
            set_num = int(parts[1])
            set_type = parts[5]
            eid = int(parts[6])
            program_set_id = int(psid) if psid.isdigit() else None
            self.log_set_handler(psid, eid, program_set_id or 0, set_num, set_type)
        except (ValueError, IndexError) as e:
            print(f"Error parsing set_info: {set_info}, error: {e}")
            return
    def request_finish(self):
        self.finish_requested = True
    def cancel_finish(self):
        self.finish_requested = False
    # -----------------------------------------------------------------------
    # Finish session
    # -----------------------------------------------------------------------
    def do_finish_session(self):
        from workout_tracker.services.workout_service import finish_session

        finish_session(self.session_id, self.session_secs)

        sets       = list(self.logged_sets.values())
        total_sets = len(sets)
        total_prs  = sum(1 for s in sets if s.get("is_pr"))
        rest_times = [s["rest_secs"] for s in sets if s.get("rest_secs")]
        total_rest = sum(rest_times)
        avg_rest   = int(total_rest / len(rest_times)) if rest_times else 0

        self.summary_data = {
            "duration_secs": self.session_secs,
            "total_sets"   : total_sets,
            "total_prs"    : total_prs,
            "total_rest"   : total_rest,
            "avg_rest"     : avg_rest,
            "day_label"    : self.selected_day_label,
        }

        self.session_started         = False
        self.session_id              = 0
        self.program_day_id          = 0
        self.last_set_time           = ""
        self.last_set_time_by_exercise = {}
        self.session_start_time      = ""
        self.first_set_logged        = False
        self.logged_sets             = {}
        self.adhoc_sets              = {}
        self.adhoc_counter           = -1
        self.last_logged_key         = ""
        self.exercise_swaps          = {}
        self.expanded_exercises      = []
        self.finish_requested        = False
        self.input_values            = {}
        self.session_secs            = 0
        self.rest_secs               = 0
        self.show_summary            = True
    def go_home(self):
        self.show_summary = False
        self.summary_data = {}
        self.load_programs()