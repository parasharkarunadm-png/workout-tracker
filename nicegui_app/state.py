from datetime import datetime


class WorkoutSession:
    """Plain Python class — no framework magic needed."""

    def __init__(self):
        self.session_started = False
        self.session_id = None
        self.program_day_id = None
        self.session_start_time = None
        self.last_set_time = None
        self.last_set_time_by_exercise = {}
        self.first_set_logged = False
        self.logged_sets = {}
        self.adhoc_sets = {}
        self.adhoc_counter = -1
        self.last_logged_key = None
        self.exercise_swaps = {}
        self.expanded_exercises = set()
        self.finish_requested = False
        self.show_summary = False
        self.summary_data = {}

    def reset(self):
        self.__init__()