import reflex as rx
from workout_tracker.state import WorkoutState
from workout_tracker.pages.log_workout import screen_select_day


def index() -> rx.Component:
    return rx.center(
        rx.cond(
            WorkoutState.session_started,
            rx.text("Screen 2 coming in R3"),
            screen_select_day(),
        )
    )


app = rx.App()
app.add_page(index, on_load=WorkoutState.load_programs)