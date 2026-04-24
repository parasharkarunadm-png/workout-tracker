import streamlit as st
from db import init_db
import log_workout

# ---------------------------------------------------------------------------
# Page config — must be the first Streamlit call in the script
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Workout Tracker",
    page_icon="🏋️",
    layout="centered",        # better for mobile
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Initialize database on every startup (safe — skips if tables exist)
# ---------------------------------------------------------------------------
init_db()

# ---------------------------------------------------------------------------
# Session state defaults — initialize once, persist across reruns
# ---------------------------------------------------------------------------
defaults = {
    "session_started":    False,
    "session_id":         None,
    "program_day_id":     None,
    "last_set_time":      None,
    "session_start_time": None,
    "first_set_logged":   False,
    "logged_sets":        {},
    "adhoc_sets":         {},
    "adhoc_counter":      -1,
    "last_logged_key":    None,   # tracks last logged set for undo
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ---------------------------------------------------------------------------
# Navigation
# ---------------------------------------------------------------------------
page = st.sidebar.radio(
    "Navigate",
    ["Log Workout", "Programs", "Analytics"],
    index=0,
)

# ---------------------------------------------------------------------------
# Page routing
# ---------------------------------------------------------------------------
if page == "Log Workout":
    st.title("Log Workout")
    log_workout.render()

elif page == "Programs":
    st.title("Programs")
    st.info("Program manager coming soon.")

elif page == "Analytics":
    st.title("Analytics")
    st.info("Analytics coming soon.")