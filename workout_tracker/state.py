import reflex as rx
from datetime import datetime
from typing import Any


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

    # --- Logged data ---
    logged_sets: dict[str, Any] = {}
    adhoc_sets: dict[int, list] = {}
    adhoc_counter: int = -1
    last_logged_key: str = ""
    last_set_time_by_exercise: dict[int, str] = {}
    exercise_swaps: dict[int, int] = {}
    expanded_exercises: list[int] = []

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

    # --- Computed timers ---
    session_secs: int = 0
    rest_secs: int = 0

    # --- Exercises for current day ---
    exercises: list[dict] = []

    # -----------------------------------------------------------------------
    # Screen 1 event handlers
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
        self.weeks = [(str(w)) for w in get_weeks(self.selected_program_id)]
        week, day = get_next_program_day(self.selected_program_id)
        self.suggested_week = week or 0
        self.suggested_day  = day or 0
        self.selected_week = str(self.suggested_week) if str(self.suggested_week) in self.weeks else (self.weeks[0] if self.weeks else "")
        self.load_days()

    def on_week_change(self, week: str):
        self.selected_week = week
        self.load_days()

    def load_days(self):
        from workout_tracker.services.workout_service import get_days, get_open_session_for_day
        self.days = get_days(self.selected_program_id, int(self.selected_week))
        if not self.days:
            return
        # Apply suggested day default
        match = next((d for d in self.days if d["day_num"] == self.suggested_day and self.selected_week == self.suggested_week), None)
        self.selected_day_id    = match["id"] if match else self.days[0]["id"]
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
            self.has_open_session   = True
            self.open_session_id    = sid
            self.open_session_date  = str(sdate)
        else:
            self.has_open_session  = False
            self.open_session_id   = 0
            self.open_session_date = ""

    def start_session(self):
        from workout_tracker.services.workout_service import create_session
        sid = create_session(self.selected_day_id)
        self._init_session(sid, self.selected_day_id, datetime.utcnow().isoformat())

    def resume_session(self):
        from workout_tracker.services.workout_service import rehydrate_session
        logged, adhoc, counter, last_key, last_at = rehydrate_session(self.open_session_id)
        self._init_session(self.open_session_id, self.selected_day_id, self.open_session_date)
        self.logged_sets     = logged
        self.adhoc_sets      = adhoc
        self.adhoc_counter   = counter
        self.last_logged_key = last_key or ""
        self.last_set_time   = last_at.isoformat() if last_at else ""
        self.first_set_logged = len(logged) > 0

    def _init_session(self, sid: int, day_id: int, start_time: str):
        self.session_id          = sid
        self.program_day_id      = day_id
        self.session_started     = True
        self.session_start_time  = start_time
        self.last_set_time       = ""
        self.first_set_logged    = False
        self.logged_sets         = {}
        self.adhoc_sets          = {}
        self.adhoc_counter       = -1
        self.last_logged_key     = ""
        self.exercise_swaps      = {}
        self.expanded_exercises  = []
        self.finish_requested    = False

    # -----------------------------------------------------------------------
    # Timer update — called by background task
    # -----------------------------------------------------------------------
    def update_timers(self):
        if self.session_start_time:
            start = datetime.fromisoformat(self.session_start_time)
            self.session_secs = int((datetime.utcnow() - start).total_seconds())
        if self.last_set_time and self.first_set_logged:
            last = datetime.fromisoformat(self.last_set_time)
            self.rest_secs = int((datetime.utcnow() - last).total_seconds())

    # -----------------------------------------------------------------------
    # Screen 2 event handlers — to be expanded in R3
    # -----------------------------------------------------------------------
    def toggle_exercise(self, eid: int):
        if eid in self.expanded_exercises:
            self.expanded_exercises.remove(eid)
        else:
            self.expanded_exercises.append(eid)

    def load_exercises(self):
        from workout_tracker.services.workout_service import get_planned_exercises
        self.exercises = get_planned_exercises(self.program_day_id)