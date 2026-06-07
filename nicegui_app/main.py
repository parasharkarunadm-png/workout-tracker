import sys
import os
import warnings
import urllib3
warnings.filterwarnings('ignore', category=urllib3.exceptions.NotOpenSSLWarning)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nicegui import ui, app
from db import init_db
from nicegui_app.state import WorkoutSession

init_db()

from fastapi import Response

def setup_theme():
    ui.dark_mode().enable()
    ui.colors(primary='red')
    ui.add_head_html('''
        <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&display=swap" rel="stylesheet">
    ''')
    ui.add_css('''
        body {
            background-color: #0a0a0a !important;
            background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.03'/%3E%3C/svg%3E");
        }

        h1, h2, h3, .nicegui-label.font-bold {
            font-family: "Bebas Neue", sans-serif !important;
            letter-spacing: 2px;
        }

        .nicegui-header {
            background-color: #1a0000 !important;
            border-bottom: 2px solid #cc0000 !important;
            padding: 12px 16px !important;
        }

        .q-card {
            background-color: #111111 !important;
            border: 1px solid #330000 !important;
            border-radius: 4px !important;
        }

        .q-card:hover {
            border-color: #cc0000 !important;
        }

        .q-btn[data-color="red"] {
            background: #cc0000 !important;
            box-shadow: 0 0 10px #cc000088 !important;
        }

        .q-btn[data-color="red"]:hover {
            box-shadow: 0 0 20px #cc0000bb !important;
        }

        .text-green-400 {
            color: #ffd700 !important;
        }

        ::-webkit-scrollbar {
            width: 4px;
        }
        ::-webkit-scrollbar-track {
            background: #0a0a0a;
        }
        ::-webkit-scrollbar-thumb {
            background: #cc0000;
        }
    ''')
    ui.add_css('''
        .q-linear-progress__track, 
        .q-linear-progress span {
            display: none !important;
        }
    ''')
@app.get('/health')
def health():
    return Response('ok')

@ui.page('/')
def index():
    setup_theme()
    session = WorkoutSession()
    from nicegui_app.log_workout import render
    render(session)


@ui.page('/logger/{day_id}/{open_sid}')
def logger(day_id: int, open_sid: int):
    setup_theme()
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