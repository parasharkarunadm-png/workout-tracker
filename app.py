import streamlit as st
from db import init_db
import log_workout
from streamlit_autorefresh import st_autorefresh

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
# Auto-refresh every 60 seconds to keep session alive and update timers
# Only active during a workout session
# ---------------------------------------------------------------------------
if st.session_state.get("session_started", False):
    st_autorefresh(interval=60000, key="session_keepalive")

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
    "show_summary":       False,
    "summary_data":       None,
    "last_set_time_by_exercise": {},
    "exercise_swaps": {},
    "expanded_exercises": set(),
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ---------------------------------------------------------------------------
# Navigation
# ---------------------------------------------------------------------------
page = st.sidebar.radio(
    "Navigate",
    ["Log Workout", "Programs", "Analytics","Admin"],
    index=0,
)
with st.sidebar:
    with st.popover("⚙️ Danger Zone"):
        st.warning("These actions cannot be undone.")
        if st.button("Clear All Sessions + Logged Sets"):
            from db import SessionLocal, Session, LoggedSet
            db = SessionLocal()
            db.query(LoggedSet).delete()
            db.query(Session).delete()
            db.commit()
            db.close()
            st.success("Cleared.")

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
    import analytics
    analytics.render()

elif page == "Admin":
    st.title("Admin")
    if st.button("Initialize DB + Seed Exercises"):
        from seed import seed_exercises
        seed_exercises()
        st.success("Done — exercises seeded.")
    import os
    st.write("DATABASE_URL:", os.environ.get("DATABASE_URL", "NOT SET"))
    st.divider()
    st.subheader("Import Program")
    program_name = st.text_input("Program Name", value="PHAT")
    source       = st.text_input("Source", value="Liftvault - PHAT by Layne Norton")
    uploaded     = st.file_uploader("Upload program Excel file", type=["xlsx"])

    if uploaded and st.button("Import Program"):
        import tempfile, os
        from importer import import_program
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            tmp.write(uploaded.read())
            tmp_path = tmp.name
        try:
            import_program(tmp_path, program_name, source)
            st.success(f"Program '{program_name}' imported successfully.")
        except Exception as e:
            st.error(f"Import failed: {e}")
        finally:
            os.remove(tmp_path)