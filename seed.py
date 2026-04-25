from db import init_db, SessionLocal
from db import Exercise

# ---------------------------------------------------------------------------
# Core exercise library — 30 exercises covering major movement patterns
# Expand in Sprint 5 to 150-200 exercises
#
# primary_muscle  : chest / back / shoulders / triceps / biceps /
#                   quads / hamstrings / glutes / calves / core
# equipment       : barbell / dumbbell / cable / machine / bodyweight
# movement_pattern: push / pull / hinge / squat / isolation
# ---------------------------------------------------------------------------

EXERCISES = [
    # --- Chest ---
    {"name": "Barbell Bench Press",       "primary_muscle": "chest",      "equipment": "barbell",    "movement_pattern": "push"},
    {"name": "Incline Barbell Press",     "primary_muscle": "chest",      "equipment": "barbell",    "movement_pattern": "push"},
    {"name": "Dumbbell Bench Press",      "primary_muscle": "chest",      "equipment": "dumbbell",   "movement_pattern": "push"},
    {"name": "Incline Dumbbell Press",    "primary_muscle": "chest",      "equipment": "dumbbell",   "movement_pattern": "push"},
    {"name": "Cable Fly",                 "primary_muscle": "chest",      "equipment": "cable",      "movement_pattern": "isolation"},
    {"name": "Chest Dip",                 "primary_muscle": "chest",      "equipment": "bodyweight", "movement_pattern": "push"},
    {"name": "Dumbbell Fly",              "primary_muscle": "chest",      "equipment": "dumbbell",   "movement_pattern": "isolation"},

    # --- Back ---
    {"name": "Barbell Row",               "primary_muscle": "back",       "equipment": "barbell",    "movement_pattern": "pull"},
    {"name": "Dumbbell Row",              "primary_muscle": "back",       "equipment": "dumbbell",   "movement_pattern": "pull"},
    {"name": "Pull Up",                   "primary_muscle": "back",       "equipment": "bodyweight", "movement_pattern": "pull"},
    {"name": "Lat Pulldown",              "primary_muscle": "back",       "equipment": "cable",      "movement_pattern": "pull"},
    {"name": "Seated Cable Row",          "primary_muscle": "back",       "equipment": "cable",      "movement_pattern": "pull"},
    {"name": "Deadlift",                  "primary_muscle": "back",       "equipment": "barbell",    "movement_pattern": "hinge"},

    # --- Shoulders ---
    {"name": "Overhead Press",            "primary_muscle": "shoulders",  "equipment": "barbell",    "movement_pattern": "push"},
    {"name": "Dumbbell Shoulder Press",   "primary_muscle": "shoulders",  "equipment": "dumbbell",   "movement_pattern": "push"},
    {"name": "Lateral Raise",             "primary_muscle": "shoulders",  "equipment": "dumbbell",   "movement_pattern": "isolation"},
    {"name": "Cable Lateral Raise",       "primary_muscle": "shoulders",  "equipment": "cable",      "movement_pattern": "isolation"},
    {"name": "Face Pull",                 "primary_muscle": "shoulders",  "equipment": "cable",      "movement_pattern": "pull"},

    # --- Triceps ---
    {"name": "Tricep Pushdown",           "primary_muscle": "triceps",    "equipment": "cable",      "movement_pattern": "isolation"},
    {"name": "Overhead Tricep Extension", "primary_muscle": "triceps",    "equipment": "cable",      "movement_pattern": "isolation"},
    {"name": "Skull Crusher",             "primary_muscle": "triceps",    "equipment": "barbell",    "movement_pattern": "isolation"},
    {"name": "One Arm Dumbbell Extension", "primary_muscle": "triceps",   "equipment": "dumbbell",   "movement_pattern": "isolation"},

    # --- Biceps ---
    {"name": "Barbell Curl",              "primary_muscle": "biceps",     "equipment": "barbell",    "movement_pattern": "isolation"},
    {"name": "Dumbbell Curl",             "primary_muscle": "biceps",     "equipment": "dumbbell",   "movement_pattern": "isolation"},
    {"name": "Cable Curl",                "primary_muscle": "biceps",     "equipment": "cable",      "movement_pattern": "isolation"},
    {"name": "Hammer Curl",               "primary_muscle": "biceps",     "equipment": "dumbbell",   "movement_pattern": "isolation"},

    # --- Chest (PHAT additions) ---
    {"name": "Incline Cable Fly",                 "primary_muscle": "chest",      "equipment": "cable",      "movement_pattern": "isolation"},
    {"name": "Incline Chest Press",               "primary_muscle": "chest",      "equipment": "machine",    "movement_pattern": "push"},

    # --- Back (PHAT additions) ---
    {"name": "Weighted Pull Up",                  "primary_muscle": "back",       "equipment": "bodyweight", "movement_pattern": "pull"},
    {"name": "Pendlay Row",                       "primary_muscle": "back",       "equipment": "barbell",    "movement_pattern": "pull"},
    {"name": "Horizontal Row",                    "primary_muscle": "back",       "equipment": "machine",    "movement_pattern": "pull"},
    {"name": "Braced Dumbbell Row",               "primary_muscle": "back",       "equipment": "dumbbell",   "movement_pattern": "pull"},
    {"name": "Close Grip Pulldown",               "primary_muscle": "back",       "equipment": "cable",      "movement_pattern": "pull"},
    {"name": "Hyperextension",               "primary_muscle": "back",       "equipment": "bodyweight",      "movement_pattern": "isolation"},

    # --- Shoulders (PHAT additions) ---
    {"name": "Upright Row",                       "primary_muscle": "shoulders",  "equipment": "barbell",    "movement_pattern": "pull"},
    {"name": "DB Side Lateral Raise",             "primary_muscle": "shoulders",  "equipment": "dumbbell",   "movement_pattern": "isolation"},
    {"name": "Bent Over Lateral Raise",             "primary_muscle": "shoulders",  "equipment": "dumbbell",   "movement_pattern": "isolation"},
    {"name": "Barbell Shrug",             "primary_muscle": "shoulders",  "equipment": "barbell",   "movement_pattern": "pull"},

    # --- Triceps (PHAT additions) ---
    {"name": "Weighted Dip",                      "primary_muscle": "triceps",    "equipment": "bodyweight", "movement_pattern": "push"},
    {"name": "Dumbbell Skull Crusher",            "primary_muscle": "triceps",    "equipment": "dumbbell",   "movement_pattern": "isolation"},
    {"name": "Cambered Bar Tricep Extension",     "primary_muscle": "triceps",    "equipment": "barbell",    "movement_pattern": "isolation"},
    {"name": "Cable Pressdown with Rope",         "primary_muscle": "triceps",    "equipment": "cable",      "movement_pattern": "isolation"},
    {"name": "Cable Kickback",                    "primary_muscle": "triceps",    "equipment": "cable",      "movement_pattern": "isolation"},

    # --- Biceps (PHAT additions) ---
    {"name": "Cambered Bar Curl",                 "primary_muscle": "biceps",     "equipment": "barbell",    "movement_pattern": "isolation"},
    {"name": "Preacher Curl",                     "primary_muscle": "biceps",     "equipment": "machine",    "movement_pattern": "isolation"},
    {"name": "Dumbbell Concentration Curl",       "primary_muscle": "biceps",     "equipment": "dumbbell",   "movement_pattern": "isolation"},
    {"name": "Spider Curl",                       "primary_muscle": "biceps",     "equipment": "dumbbell",   "movement_pattern": "isolation"},

    # --- Legs ---
    {"name": "Barbell Squat",             "primary_muscle": "quads",      "equipment": "barbell",    "movement_pattern": "squat"},
    {"name": "Leg Press",                 "primary_muscle": "quads",      "equipment": "machine",    "movement_pattern": "squat"},
    {"name": "Romanian Deadlift",         "primary_muscle": "hamstrings", "equipment": "barbell",    "movement_pattern": "hinge"},
    {"name": "Leg Curl",                  "primary_muscle": "hamstrings", "equipment": "machine",    "movement_pattern": "isolation"},
    {"name": "Hip Thrust",                "primary_muscle": "glutes",     "equipment": "barbell",    "movement_pattern": "hinge"},
    {"name": "Calf Raise",                "primary_muscle": "calves",     "equipment": "machine",    "movement_pattern": "isolation"},

    # --- Legs (PHAT additions) ---
    {"name": "Hack Squat",                        "primary_muscle": "quads",      "equipment": "machine",    "movement_pattern": "squat"},
    {"name": "Leg Extension",                     "primary_muscle": "quads",      "equipment": "machine",    "movement_pattern": "isolation"},
    {"name": "Stiff Legged Deadlift",             "primary_muscle": "hamstrings", "equipment": "barbell",    "movement_pattern": "hinge"},
    {"name": "Lying Leg Curl",                    "primary_muscle": "hamstrings", "equipment": "machine",    "movement_pattern": "isolation"},
    {"name": "Seated Leg Curl",                   "primary_muscle": "hamstrings", "equipment": "machine",    "movement_pattern": "isolation"},
    {"name": "Standing Calf Raise",               "primary_muscle": "calves",     "equipment": "machine",    "movement_pattern": "isolation"},
    {"name": "Seated Calf Raise",                 "primary_muscle": "calves",     "equipment": "machine",    "movement_pattern": "isolation"},
    {"name": "Donkey Calf Raise",                 "primary_muscle": "calves",     "equipment": "machine",    "movement_pattern": "isolation"},
]


def seed_exercises():
    init_db()
    db = SessionLocal()

    added, skipped = 0, 0

    for ex in EXERCISES:
        # Check if exercise already exists by name — safe to re-run
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