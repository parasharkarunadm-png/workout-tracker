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
    "session_started": False,   # controls Screen 1 vs Screen 2
    "session_id":      None,    # active Session row id
    "program_day_id":  None,    # locked-in program day
    "last_set_time":   None,    # timestamp for rest timer
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