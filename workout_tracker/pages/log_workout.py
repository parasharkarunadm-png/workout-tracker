import reflex as rx
from workout_tracker.state import WorkoutState


def fmt_duration(seconds: int) -> str:
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02}:{m:02}:{s:02}"


def screen_select_day() -> rx.Component:
    return rx.vstack(
        rx.heading("Select Today's Workout", size="5"),

        rx.select(
            WorkoutState.programs.foreach(lambda p: p["name"]),
            value=WorkoutState.selected_program_name,
            on_change=WorkoutState.on_program_change,
            width="100%",
        ),

        rx.select(
            WorkoutState.weeks,
            value=WorkoutState.selected_week,
            on_change=WorkoutState.on_week_change,
            placeholder="Select a week",
            width="100%",
        ),

        rx.select(
            WorkoutState.days.foreach(lambda d: d["label"]),
            value=WorkoutState.selected_day_label,
            on_change=WorkoutState.on_day_change,
            width="100%",
        ),

        rx.cond(
            WorkoutState.suggested_week > 0,
            rx.text("💡 Suggested based on your last session", size="1", color="gray"),
        ),

        rx.divider(),

        rx.cond(
            WorkoutState.has_open_session,
            rx.vstack(
                rx.callout("An open session exists for today. Resume it?", icon="triangle_alert"),
                rx.hstack(
                    rx.button("Resume Session", on_click=WorkoutState.resume_session, color_scheme="blue", width="50%"),
                    rx.button("Start Fresh", on_click=WorkoutState.start_session, variant="outline", width="50%"),
                    width="100%",
                ),
                width="100%",
            ),
            rx.button("Start Session", on_click=WorkoutState.start_session, color_scheme="blue", width="100%"),
        ),

        width="100%",
        max_width="480px",
        padding="16px",
        spacing="4",
    )