import reflex as rx
from workout_tracker.state import WorkoutState


# ---------------------------------------------------------------------------
# Exercise card — renders from encoded header string "index||name||set_count"
# ---------------------------------------------------------------------------
def exercise_card(header: str) -> rx.Component:
    """Display exercise header and sets when expanded."""
    display_label = WorkoutState.exercise_display_labels[header]
    
    return rx.vstack(
        rx.hstack(
            rx.button(
                display_label,
                variant="ghost",
                on_click=WorkoutState.toggle_exercise_by_header(header),
                width="85%",
                justify="start",
            ),
            rx.button(
                "🔄", 
                variant="ghost", 
                width="15%",
                on_click=lambda: WorkoutState.handle_swap(header),
            ),
            width="100%",
        ),
        rx.cond(
            WorkoutState.expanded_header == header,
            rx.vstack(
                rx.text(WorkoutState.last_best, size="1", color="gray"),
                rx.foreach(WorkoutState.expanded_exercise_sets, set_row),
                padding_left="8px",
                width="100%",
            ),
        ),
        rx.divider(),
        width="100%",
    )


# ---------------------------------------------------------------------------
# Set inputs — renders planned sets for a given exercise_id
# ---------------------------------------------------------------------------
def set_row(set_info: str) -> rx.Component:
    """Render a single set row with pre-computed labels from state."""
    
    # Extract psid from set_info at component definition time
    psid = set_info.split("|")[0]
    
    # Look up pre-computed label and psid from state maps
    set_label = WorkoutState.expanded_set_labels_map[set_info]
    
    is_logged = WorkoutState.logged_sets.contains(psid)
    
    return rx.cond(
        is_logged,
        rx.box(
            rx.text("✅ Set logged", color="green", size="2"),
            width="100%",
            padding_y="4px",
        ),
        rx.vstack(
            rx.text(set_label, size="2", weight="bold"),
            rx.hstack(
                rx.input(
                    placeholder="lb",
                    type="number",
                    on_change=lambda v: WorkoutState.update_input(psid, "weight", v),
                    width="25%",
                ),
                rx.input(
                    placeholder="Reps",
                    type="number",
                    on_change=lambda v: WorkoutState.update_input(psid, "reps", v),
                    width="25%",
                ),
                rx.input(
                    placeholder="RIR",
                    type="number",
                    on_change=lambda v: WorkoutState.update_input(psid, "rir", v),
                    width="20%",
                ),
                rx.button(
                    "Log",
                    on_click=lambda: WorkoutState.log_set_from_string(set_info),
                    color_scheme="red",
                    width="25%",
                    size="2",
                ),
                width="100%",
                spacing="2",
            ),
            width="100%",
            padding_y="4px",
        ),
    )


def set_inputs_for_exercise(eid: int) -> rx.Component:
    """Render set rows for a specific exercise using encoded set strings."""
    return rx.foreach(
        WorkoutState.get_set_strings_for_exercise(eid),
        set_row,
    )


# ---------------------------------------------------------------------------
# Screens
# ---------------------------------------------------------------------------
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


def screen_logger() -> rx.Component:
    return rx.vstack(
        rx.heading(WorkoutState.selected_day_label, size="5"),
        rx.hstack(
            rx.vstack(
                rx.text("Session", size="1", color="gray"),
                rx.text(WorkoutState.session_time_display, weight="bold"),
            ),
            rx.vstack(
                rx.text("Rest", size="1", color="gray"),
                rx.text(WorkoutState.rest_time_display, weight="bold"),
            ),
            justify="between",
            width="100%",
        ),
        rx.divider(),
        rx.foreach(WorkoutState.exercise_headers, exercise_card),
        rx.divider(),
        rx.cond(
            WorkoutState.finish_requested,
            rx.vstack(
                rx.text("Finish session?", weight="bold"),
                rx.hstack(
                    rx.button("Confirm", on_click=WorkoutState.do_finish_session, color_scheme="blue", width="50%"),
                    rx.button("Cancel", on_click=WorkoutState.cancel_finish, width="50%"),
                    width="100%",
                ),
                width="100%",
            ),
            rx.vstack(
                rx.cond(
                    WorkoutState.last_logged_key != "",
                    rx.button("↩️ Undo Last Set", on_click=WorkoutState.undo_handler, width="100%", variant="outline"),
                ),
                rx.button("Finish Session", on_click=WorkoutState.request_finish, color_scheme="blue", width="100%"),
                width="100%",
            ),
        ),
        width="100%",
        max_width="480px",
        padding="16px",
        spacing="4",
    )


def screen_summary() -> rx.Component:
    return rx.vstack(
        rx.heading("✅ Session Complete", size="6"),
        rx.divider(),
        rx.hstack(
            rx.vstack(
                rx.text("Duration", size="1", color="gray"),
                rx.text(WorkoutState.session_time_display, weight="bold"),
            ),
            rx.vstack(
                rx.text("Sets", size="1", color="gray"),
                rx.text(WorkoutState.total_sets_summary.to_string(), weight="bold"),
            ),
            rx.vstack(
                rx.text("PRs", size="1", color="gray"),
                rx.text(WorkoutState.total_prs_summary.to_string(), weight="bold"),
            ),
            justify="between",
            width="100%",
        ),
        rx.button("Back to Home", on_click=WorkoutState.go_home, color_scheme="blue", width="100%"),
        width="100%",
        max_width="480px",
        padding="16px",
        spacing="4",
    )