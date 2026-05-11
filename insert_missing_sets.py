from db import SessionLocal, LoggedSet
from datetime import datetime

SESSION_ID = 19

SETS_TO_INSERT = [
    # Machine Dip
    {"session_id": SESSION_ID, "exercise_id": 67, "program_set_id": None, "set_num": 1, "weight_lb": 140.0, "reps": 10, "rir": None, "rest_secs": 0,   "is_pr": False, "set_type": "working"},
    {"session_id": SESSION_ID, "exercise_id": 67, "program_set_id": None, "set_num": 2, "weight_lb": 140.0, "reps": 10, "rir": None, "rest_secs": 92,  "is_pr": False, "set_type": "working"},

    # Pendlay Row
    {"session_id": SESSION_ID, "exercise_id": 30, "program_set_id": None, "set_num": 1, "weight_lb": 115.0, "reps": 5,  "rir": None, "rest_secs": 0,   "is_pr": False, "set_type": "working"},
    {"session_id": SESSION_ID, "exercise_id": 30, "program_set_id": None, "set_num": 2, "weight_lb": 125.0, "reps": 5,  "rir": None, "rest_secs": 105, "is_pr": False, "set_type": "working"},
    {"session_id": SESSION_ID, "exercise_id": 30, "program_set_id": None, "set_num": 3, "weight_lb": 125.0, "reps": 5,  "rir": None, "rest_secs": 93,  "is_pr": False, "set_type": "working"},

    # Dumbbell Shoulder Press
    {"session_id": SESSION_ID, "exercise_id": 15, "program_set_id": None, "set_num": 1, "weight_lb": 25.0,  "reps": 10, "rir": None, "rest_secs": 0,   "is_pr": False, "set_type": "working"},
    {"session_id": SESSION_ID, "exercise_id": 15, "program_set_id": None, "set_num": 2, "weight_lb": 37.5,  "reps": 10, "rir": None, "rest_secs": 81,  "is_pr": False, "set_type": "working"},
    {"session_id": SESSION_ID, "exercise_id": 15, "program_set_id": None, "set_num": 3, "weight_lb": 37.5,  "reps": 9,  "rir": None, "rest_secs": 104, "is_pr": False, "set_type": "working"},

    # Cambered Bar Curl
    {"session_id": SESSION_ID, "exercise_id": 44, "program_set_id": None, "set_num": 1, "weight_lb": 50.0,  "reps": 10, "rir": None, "rest_secs": 0,   "is_pr": False, "set_type": "working"},
    {"session_id": SESSION_ID, "exercise_id": 44, "program_set_id": None, "set_num": 2, "weight_lb": 60.0,  "reps": 10, "rir": None, "rest_secs": 59,  "is_pr": False, "set_type": "working"},
    {"session_id": SESSION_ID, "exercise_id": 44, "program_set_id": None, "set_num": 3, "weight_lb": 55.0,  "reps": 10, "rir": None, "rest_secs": 94,  "is_pr": False, "set_type": "working"},

    # Skull Crusher
    {"session_id": SESSION_ID, "exercise_id": 21, "program_set_id": None, "set_num": 1, "weight_lb": 50.0,  "reps": 10, "rir": None, "rest_secs": 0,   "is_pr": False, "set_type": "working"},
    {"session_id": SESSION_ID, "exercise_id": 21, "program_set_id": None, "set_num": 2, "weight_lb": 50.0,  "reps": 10, "rir": None, "rest_secs": 61,  "is_pr": False, "set_type": "working"},
    {"session_id": SESSION_ID, "exercise_id": 21, "program_set_id": None, "set_num": 3, "weight_lb": 50.0,  "reps": 9,  "rir": None, "rest_secs": 81,  "is_pr": False, "set_type": "working"},
]


def insert_sets():
    db = SessionLocal()
    added = 0
    for s in SETS_TO_INSERT:
        entry = LoggedSet(
            session_id     = s["session_id"],
            exercise_id    = s["exercise_id"],
            program_set_id = s["program_set_id"],
            set_num        = s["set_num"],
            weight_lb      = s["weight_lb"],
            reps           = s["reps"],
            rir            = s["rir"],
            rest_secs      = s["rest_secs"],
            is_pr          = s["is_pr"],
            set_type       = s["set_type"],
            logged_at      = datetime.utcnow(),
        )
        db.add(entry)
        added += 1
    db.commit()
    db.close()
    print(f"Done — {added} sets inserted into session {SESSION_ID}.")


if __name__ == "__main__":
    insert_sets()