import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nicegui import ui, app
from db import init_db
from nicegui_app.state import WorkoutSession

init_db()

from fastapi import Response

@app.get('/health')
def health():
    return Response('ok')

@ui.page('/')
def index():
    session = WorkoutSession()
    from nicegui_app.log_workout import render
    render(session)


@ui.page('/logger/{day_id}/{open_sid}')
def logger(day_id: int, open_sid: int):
    from nicegui_app.log_workout import screen_logger
    session = WorkoutSession()
    screen_logger(session, day_id, open_sid if open_sid != 0 else None)

ui.run(
    title='Workout Tracker',
    host='0.0.0.0',
    port=int(os.environ.get('PORT', 8080)),
    reload=False,
    storage_secret='workout_tracker_secret',
)