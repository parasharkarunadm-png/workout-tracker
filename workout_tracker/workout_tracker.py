import reflex as rx
from workout_tracker.state import WorkoutState
from workout_tracker.pages.log_workout import screen_select_day, screen_logger, screen_summary


def index() -> rx.Component:
    return rx.center(
        rx.cond(
            WorkoutState.show_summary,
            screen_summary(),
            rx.cond(
                WorkoutState.session_started,
                screen_logger(),
                screen_select_day(),
            ),
        ),
        min_height="100vh",
    )


app = rx.App()
app.add_page(index, on_load=WorkoutState.load_programs)