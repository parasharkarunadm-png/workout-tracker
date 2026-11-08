from db import init_db, SessionLocal
from db import Exercise

# ---------------------------------------------------------------------------
# Core exercise library — 55 exercises covering major movement patterns
# Expand in Sprint 5 to 150-200 exercises
#
# primary_muscle  : chest / back / shoulders / triceps / biceps /
#                   quads / hamstrings / glutes / calves / core
# equipment       : barbell / dumbbell / cable / machine / bodyweight
# movement_pattern: push_horizontal / push_vertical / pull_horizontal /
#                   pull_vertical / hinge / squat / isolation
# ---------------------------------------------------------------------------

EXERCISES = [
    # --- Chest ---
    {"name": "Barbell Bench Press",           "primary_muscle": "chest",      "equipment": "barbell",    "movement_pattern": "push_horizontal"},
    {"name": "Incline Barbell Press",         "primary_muscle": "chest",      "equipment": "barbell",    "movement_pattern": "push_horizontal"},
    {"name": "Dumbbell Bench Press",          "primary_muscle": "chest",      "equipment": "dumbbell",   "movement_pattern": "push_horizontal"},
    {"name": "Incline Dumbbell Press",        "primary_muscle": "chest",      "equipment": "dumbbell",   "movement_pattern": "push_horizontal"},
    {"name": "Cable Fly",                     "primary_muscle": "chest",      "equipment": "cable",      "movement_pattern": "isolation"},
    {"name": "Chest Dip",                     "primary_muscle": "chest",      "equipment": "bodyweight", "movement_pattern": "push_horizontal"},
    {"name": "Dumbbell Fly",                  "primary_muscle": "chest",      "equipment": "dumbbell",   "movement_pattern": "isolation"},
    {"name": "Incline Cable Fly",             "primary_muscle": "chest",      "equipment": "cable",      "movement_pattern": "isolation"},
    {"name": "Incline Chest Press",           "primary_muscle": "chest",      "equipment": "machine",    "movement_pattern": "push_horizontal"},
    {"name": "Machine Chest Press",   "primary_muscle": "chest",     "equipment": "machine", "movement_pattern": "push_horizontal"},

    # --- Back ---
    {"name": "Barbell Row",                   "primary_muscle": "back",       "equipment": "barbell",    "movement_pattern": "pull_horizontal"},
    {"name": "Dumbbell Row",                  "primary_muscle": "back",       "equipment": "dumbbell",   "movement_pattern": "pull_horizontal"},
    {"name": "Pull Up",                       "primary_muscle": "back",       "equipment": "bodyweight", "movement_pattern": "pull_vertical"},
    {"name": "Lat Pulldown",                  "primary_muscle": "back",       "equipment": "cable",      "movement_pattern": "pull_vertical"},
    {"name": "Seated Cable Row",              "primary_muscle": "back",       "equipment": "cable",      "movement_pattern": "pull_horizontal"},
    {"name": "Deadlift",                      "primary_muscle": "back",       "equipment": "barbell",    "movement_pattern": "hinge"},
    {"name": "Weighted Pull Up",              "primary_muscle": "back",       "equipment": "bodyweight", "movement_pattern": "pull_vertical"},
    {"name": "Pendlay Row",                   "primary_muscle": "back",       "equipment": "barbell",    "movement_pattern": "pull_horizontal"},
    {"name": "Horizontal Row",                "primary_muscle": "back",       "equipment": "machine",    "movement_pattern": "pull_horizontal"},
    {"name": "Braced Dumbbell Row",           "primary_muscle": "back",       "equipment": "dumbbell",   "movement_pattern": "pull_horizontal"},
    {"name": "Close Grip Pulldown",           "primary_muscle": "back",       "equipment": "cable",      "movement_pattern": "pull_vertical"},
    {"name": "Hyperextension",                "primary_muscle": "back",       "equipment": "bodyweight", "movement_pattern": "hinge"},
    {"name": "Machine Row",           "primary_muscle": "back",      "equipment": "machine", "movement_pattern": "pull_horizontal"},
    {"name": "Machine Pulldown",      "primary_muscle": "back",      "equipment": "machine", "movement_pattern": "pull_vertical"},

    # --- Shoulders ---
    {"name": "Overhead Press",                "primary_muscle": "shoulders",  "equipment": "barbell",    "movement_pattern": "push_vertical"},
    {"name": "Dumbbell Shoulder Press",       "primary_muscle": "shoulders",  "equipment": "dumbbell",   "movement_pattern": "push_vertical"},
    {"name": "Lateral Raise",                 "primary_muscle": "shoulders",  "equipment": "dumbbell",   "movement_pattern": "isolation"},
    {"name": "Cable Lateral Raise",           "primary_muscle": "shoulders",  "equipment": "cable",      "movement_pattern": "isolation"},
    {"name": "Face Pull",                     "primary_muscle": "shoulders",  "equipment": "cable",      "movement_pattern": "pull_horizontal"},
    {"name": "Upright Row",                   "primary_muscle": "shoulders",  "equipment": "barbell",    "movement_pattern": "pull_vertical"},
    {"name": "Bent Over Lateral Raise",       "primary_muscle": "shoulders",  "equipment": "dumbbell",   "movement_pattern": "isolation"},
    {"name": "Barbell Shrug",                 "primary_muscle": "shoulders",  "equipment": "barbell",    "movement_pattern": "isolation"},
    {"name": "Machine Shoulder Press","primary_muscle": "shoulders", "equipment": "machine", "movement_pattern": "push_vertical"},
    {"name": "Machine Lateral Raise", "primary_muscle": "shoulders", "equipment": "machine", "movement_pattern": "isolation"},

    # --- Triceps ---
    {"name": "Tricep Pushdown",               "primary_muscle": "triceps",    "equipment": "cable",      "movement_pattern": "isolation"},
    {"name": "Overhead Tricep Extension",     "primary_muscle": "triceps",    "equipment": "cable",      "movement_pattern": "isolation"},
    {"name": "Skull Crusher",                 "primary_muscle": "triceps",    "equipment": "barbell",    "movement_pattern": "isolation"},
    {"name": "One Arm Dumbbell Extension",    "primary_muscle": "triceps",    "equipment": "dumbbell",   "movement_pattern": "isolation"},
    {"name": "Weighted Dip",                  "primary_muscle": "triceps",    "equipment": "bodyweight", "movement_pattern": "push_horizontal"},
    {"name": "Dumbbell Skull Crusher",        "primary_muscle": "triceps",    "equipment": "dumbbell",   "movement_pattern": "isolation"},
    {"name": "Cambered Bar Tricep Extension", "primary_muscle": "triceps",    "equipment": "barbell",    "movement_pattern": "isolation"},
    {"name": "Cable Pressdown with Rope",     "primary_muscle": "triceps",    "equipment": "cable",      "movement_pattern": "isolation"},
    {"name": "Cable Kickback",                "primary_muscle": "triceps",    "equipment": "cable",      "movement_pattern": "isolation"},
    {"name": "Machine Dip",           "primary_muscle": "triceps",   "equipment": "machine", "movement_pattern": "push_horizontal"},
    {"name": "Machine Tricep Extension","primary_muscle": "triceps", "equipment": "machine", "movement_pattern": "isolation"},


    # --- Biceps ---
    {"name": "Barbell Curl",                  "primary_muscle": "biceps",     "equipment": "barbell",    "movement_pattern": "isolation"},
    {"name": "Dumbbell Curl",                 "primary_muscle": "biceps",     "equipment": "dumbbell",   "movement_pattern": "isolation"},
    {"name": "Cable Curl",                    "primary_muscle": "biceps",     "equipment": "cable",      "movement_pattern": "isolation"},
    {"name": "Hammer Curl",                   "primary_muscle": "biceps",     "equipment": "dumbbell",   "movement_pattern": "isolation"},
    {"name": "Cambered Bar Curl",             "primary_muscle": "biceps",     "equipment": "barbell",    "movement_pattern": "isolation"},
    {"name": "Preacher Curl",                 "primary_muscle": "biceps",     "equipment": "machine",    "movement_pattern": "isolation"},
    {"name": "Dumbbell Concentration Curl",   "primary_muscle": "biceps",     "equipment": "dumbbell",   "movement_pattern": "isolation"},
    {"name": "Spider Curl",                   "primary_muscle": "biceps",     "equipment": "dumbbell",   "movement_pattern": "isolation"},
    {"name": "Machine Curl",          "primary_muscle": "biceps",    "equipment": "machine", "movement_pattern": "isolation"},

    # --- Legs ---
    {"name": "Barbell Squat",                 "primary_muscle": "quads",      "equipment": "barbell",    "movement_pattern": "squat"},
    {"name": "Squat",                         "primary_muscle": "quads",      "equipment": "barbell",    "movement_pattern": "squat"},
    {"name": "Leg Press",                     "primary_muscle": "quads",      "equipment": "machine",    "movement_pattern": "squat"},
    {"name": "Hack Squat",                    "primary_muscle": "quads",      "equipment": "machine",    "movement_pattern": "squat"},
    {"name": "Leg Extension",                 "primary_muscle": "quads",      "equipment": "machine",    "movement_pattern": "isolation"},
    {"name": "Romanian Deadlift",             "primary_muscle": "hamstrings", "equipment": "barbell",    "movement_pattern": "hinge"},
    {"name": "Stiff Legged Deadlift",         "primary_muscle": "hamstrings", "equipment": "barbell",    "movement_pattern": "hinge"},
    {"name": "Leg Curl",                      "primary_muscle": "hamstrings", "equipment": "machine",    "movement_pattern": "isolation"},
    {"name": "Lying Leg Curl",                "primary_muscle": "hamstrings", "equipment": "machine",    "movement_pattern": "isolation"},
    {"name": "Seated Leg Curl",               "primary_muscle": "hamstrings", "equipment": "machine",    "movement_pattern": "isolation"},
    {"name": "Hip Thrust",                    "primary_muscle": "glutes",     "equipment": "barbell",    "movement_pattern": "hinge"},
    {"name": "Standing Calf Raise",           "primary_muscle": "calves",     "equipment": "machine",    "movement_pattern": "isolation"},
    {"name": "Seated Calf Raise",             "primary_muscle": "calves",     "equipment": "machine",    "movement_pattern": "isolation"},
    {"name": "Donkey Calf Raise",             "primary_muscle": "calves",     "equipment": "machine",    "movement_pattern": "isolation"},
    {"name": "Dumbbell Lateral Raise",        "primary_muscle": "shoulders",  "equipment": "dumbbell",   "movement_pattern": "isolation"},
    {"name": "Eccentric Heel Drop",           "primary_muscle": "calves",     "equipment": "bodyweight", "movement_pattern": "isolation"},
    {"name": "Single Leg Romanian Deadlift",  "primary_muscle": "hamstrings", "equipment": "dumbbell",   "movement_pattern": "hinge"},
    {"name": "Tibialis Anterior Raise",       "primary_muscle": "tibialis anterior", "equipment": "bodyweight", "movement_pattern": "isolation"},
]


def seed_exercises():
    init_db()
    db = SessionLocal()

    added, skipped = 0, 0

    for ex in EXERCISES:
        exists = db.query(Exercise).filter_by(name=ex["name"]).first()
        if exists:
            skipped += 1
            continue

        db.add(Exercise(**ex))
        added += 1

    db.commit()
    db.close()

    print(f"Done — {added} exercises added, {skipped} already existed.")


if __name__ == "__main__":
    seed_exercises()