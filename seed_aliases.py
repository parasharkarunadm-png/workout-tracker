from db import init_db, SessionLocal, Exercise

# ---------------------------------------------------------------------------
# Aliases — maps common name variants (lowercase) to canonical exercise names
# Covers: program import matching + future fuzzy UI search
# Sources: PHAT (Layne Norton), Dorian Yates 1987-1992, Beast Slayer 2.0
# ---------------------------------------------------------------------------

ALIASES = {
    # --- Barbell Bench Press ---
    "Barbell Bench Press": [
        "bench press", "barbell bench", "flat bench press",
        "flat barbell press", "bb bench press", "bb bench",
    ],

    # --- Incline Barbell Press ---
    "Incline Barbell Press": [
        "incline press", "incline barbell bench press",
        "incline bench press", "incline bb press",
    ],

    # --- Dumbbell Bench Press ---
    "Dumbbell Bench Press": [
        "db bench press", "dumbbell bench", "flat db press",
        "flat dumbbell press",
    ],

    # --- Incline Dumbbell Press ---
    "Incline Dumbbell Press": [
        "incline db press", "incline dumbbell bench press",
        "incline dumbbell bench",
    ],

    # --- Chest Dip ---
    "Chest Dip": [
        "dips", "chest dips", "parallel bar dip",
    ],

    # --- Dumbbell Fly ---
    "Dumbbell Fly": [
        "db fly", "dumbbell flys", "dumbbell flies",
        "flat db fly", "flat dumbbell fly", "flat dumbbell flies",
    ],

    # --- Cable Fly ---
    "Cable Fly": [
        "cable crossover", "cable flies", "cable flys",
        "pec deck", "chest cable fly",
    ],

    # --- Incline Cable Fly ---
    "Incline Cable Fly": [
        "incline cable flies", "incline cable flys",
        "incline cable crossover",
    ],

    # --- Incline Chest Press ---
    "Incline Chest Press": [
        "incline machine press", "incline press machine",
        "machine incline press",
    ],

    # --- Barbell Row ---
    "Barbell Row": [
        "bb row", "bent over row", "bent over barbell row",
        "barbell bent over row", "overhand barbell row",
    ],

    # --- Dumbbell Row ---
    "Dumbbell Row": [
        "db row", "one arm db row", "single arm dumbbell row",
        "one arm dumbbell row",
    ],

    # --- Pull Up ---
    "Pull Up": [
        "pullup", "pull-up", "bodyweight pull up",
        "wide grip pull up", "overhand pull up",
    ],

    # --- Weighted Pull Up ---
    "Weighted Pull Up": [
        "weighted pullup", "weighted pull-up", "weighted chins",
        "weighted chin up", "weighted chinup",
    ],

    # --- Lat Pulldown ---
    "Lat Pulldown": [
        "pulldown", "lat pull down", "wide grip pulldown",
        "wide grip lat pulldown", "overhand pulldown",
    ],

    # --- Close Grip Pulldown ---
    "Close Grip Pulldown": [
        "close grip pull down", "close grip lat pulldown",
        "close grip pulldowns", "close grip pull downs",
        "narrow grip pulldown",
    ],

    # --- Seated Cable Row ---
    "Seated Cable Row": [
        "cable row", "seated row", "low cable row",
        "seated cable rows",
    ],

    # --- Pendlay Row ---
    "Pendlay Row": [
        "pendlay rows", "strict barbell row",
    ],

    # --- Horizontal Row ---
    "Horizontal Row": [
        "machine row", "chest supported row", "t-bar row",
        "t bar row",
    ],

    # --- Braced Dumbbell Row ---
    "Braced Dumbbell Row": [
        "chest supported db row", "incline db row",
        "supported dumbbell row",
    ],

    # --- Deadlift ---
    "Deadlift": [
        "conventional deadlift", "barbell deadlift",
        "bb deadlift", "pull",
    ],

    # --- Hyperextension ---
    "Hyperextension": [
        "hyperextensions", "back extension", "back extensions",
        "45 degree back extension",
    ],

    # --- Overhead Press ---
    "Overhead Press": [
        "ohp", "barbell ohp", "military press",
        "barbell overhead press", "standing press",
        "barbell shoulder press", "strict press",
    ],

    # --- Dumbbell Shoulder Press ---
    "Dumbbell Shoulder Press": [
        "db shoulder press", "seated db press",
        "seated dumbbell press", "db overhead press",
        "dumbbell overhead press",
    ],

    # --- Lateral Raise ---
    "Lateral Raise": [
        "side lateral raise", "dumbbell lateral raise",
        "db lateral raise", "side raise",
    ],

    # --- Cable Lateral Raise ---
    "Cable Lateral Raise": [
        "cable side raise", "cable side lateral raise",
    ],

    # --- Bent Over Lateral Raise ---
    "Bent Over Lateral Raise": [
        "rear delt fly", "rear delt raise", "bent over rear delt",
        "reverse fly", "reverse dumbbell fly",
        "seated bent over lateral raises", "bent over lateral raises",
        "seated dumbbell lateral raises",
    ],

    # --- Face Pull ---
    "Face Pull": [
        "face pulls", "cable face pull",
    ],

    # --- Upright Row ---
    "Upright Row": [
        "barbell upright row", "upright rows",
        "bb upright row",
    ],

    # --- Barbell Shrug ---
    "Barbell Shrug": [
        "shrug", "shrugs", "barbell shrugs",
        "bb shrug", "bb shrugs",
    ],

    # --- Tricep Pushdown ---
    "Tricep Pushdown": [
        "pushdown", "tricep push down", "cable pushdown",
        "cable tricep pushdown", "rope pushdown",
    ],

    # --- Cable Pressdown with Rope ---
    "Cable Pressdown with Rope": [
        "rope pressdown", "tricep rope pressdown",
        "cable rope pressdown", "cable extensions",
        "rope tricep extension",
    ],

    # --- Overhead Tricep Extension ---
    "Overhead Tricep Extension": [
        "cable overhead extension", "overhead cable extension",
        "overhead tricep", "cable overhead tricep extension",
    ],

    # --- Skull Crusher ---
    "Skull Crusher": [
        "skull crushers", "lying tricep extension",
        "lying tricep extensions", "ez bar skull crusher",
        "barbell skull crusher",
    ],

    # --- Dumbbell Skull Crusher ---
    "Dumbbell Skull Crusher": [
        "db skull crusher", "db skull crushers",
        "lying dumbbell tricep extension",
    ],

    # --- One Arm Dumbbell Extension ---
    "One Arm Dumbbell Extension": [
        "one arm db extension", "single arm dumbbell extension",
        "one arm dumbbell extensions", "db one arm extension",
    ],

    # --- Weighted Dip ---
    "Weighted Dip": [
        "weighted dips", "dips weighted",
    ],

    # --- Cambered Bar Tricep Extension ---
    "Cambered Bar Tricep Extension": [
        "ez bar tricep extension", "cambered bar extension",
        "ez bar extension",
    ],

    # --- Barbell Curl ---
    "Barbell Curl": [
        "bb curl", "barbell curls", "straight bar curl",
        "ez bar curl",
    ],

    # --- Dumbbell Curl ---
    "Dumbbell Curl": [
        "db curl", "dumbbell curls", "alternating dumbbell curl",
        "standing dumbbell curl",
    ],

    # --- Dumbbell Concentration Curl ---
    "Dumbbell Concentration Curl": [
        "concentration curl", "concentration curls",
        "db concentration curl",
    ],

    # --- Preacher Curl ---
    "Preacher Curl": [
        "machine preacher curl", "ez bar preacher curl",
        "scott curl",
    ],

    # --- Cambered Bar Curl ---
    "Cambered Bar Curl": [
        "ez bar preacher curl", "cambered curl",
        "ez curl", "ez-bar curl",
    ],

    # --- Barbell Squat ---
    "Barbell Squat": [
        "squat", "back squat", "barbell back squat",
        "bb squat", "high bar squat", "low bar squat",
        "smith machine squat", "hack squats or smith machine squats",
    ],

    # --- Leg Press ---
    "Leg Press": [
        "45 degree leg press", "machine leg press",
        "horizontal leg press",
    ],

    # --- Hack Squat ---
    "Hack Squat": [
        "hack squats", "machine hack squat",
        "pendulum squat",
    ],

    # --- Leg Extension ---
    "Leg Extension": [
        "leg extensions", "machine leg extension",
        "quad extension",
    ],

    # --- Romanian Deadlift ---
    "Romanian Deadlift": [
        "rdl", "barbell rdl", "romanian dl",
    ],

    # --- Stiff Legged Deadlift ---
    "Stiff Legged Deadlift": [
        "stiff leg deadlift", "stiff leg dl",
        "stiff legged dl", "sldl", "stiff leg deadlifts",
    ],

    # --- Leg Curl ---
    "Leg Curl": [
        "machine leg curl", "hamstring curl",
        "leg curls",
    ],

    # --- Lying Leg Curl ---
    "Lying Leg Curl": [
        "prone leg curl", "lying hamstring curl",
        "lying leg curls",
    ],

    # --- Seated Leg Curl ---
    "Seated Leg Curl": [
        "seated hamstring curl", "seated leg curls",
    ],

    # --- Hip Thrust ---
    "Hip Thrust": [
        "barbell hip thrust", "bb hip thrust",
        "glute bridge", "barbell glute bridge",
    ],

    # --- Standing Calf Raise ---
    "Standing Calf Raise": [
        "standing calf raises", "machine calf raise",
        "calf raise", "calf raises",
    ],

    # --- Seated Calf Raise ---
    "Seated Calf Raise": [
        "seated calf raises", "machine seated calf raise",
    ],

    # --- Donkey Calf Raise ---
    "Donkey Calf Raise": [
        "donkey calf raises",
    ],
}


def seed_aliases():
    init_db()
    db = SessionLocal()

    added, skipped, missing = 0, 0, []

    for canonical_name, aliases in ALIASES.items():
        exercise = db.query(Exercise).filter_by(name=canonical_name).first()
        if not exercise:
            missing.append(canonical_name)
            continue

        for alias in aliases:
            alias_lower = alias.strip().lower()
            from db import ExerciseAlias
            exists = db.query(ExerciseAlias).filter_by(alias=alias_lower).first()
            if exists:
                skipped += 1
                continue
            db.add(ExerciseAlias(exercise_id=exercise.id, alias=alias_lower))
            added += 1

    db.commit()
    db.close()

    print(f"Done — {added} aliases added, {skipped} already existed.")
    if missing:
        print(f"WARNING — canonical exercises not found in DB ({len(missing)}):")
        for m in missing:
            print(f"  - {m}")


if __name__ == "__main__":
    seed_aliases()