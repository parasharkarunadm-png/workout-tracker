from db import init_db, SessionLocal, Exercise

MOVEMENT_PATTERN_UPDATES = {
    # Chest
    "Barbell Bench Press"          : "push_horizontal",
    "Incline Barbell Press"        : "push_horizontal",
    "Dumbbell Bench Press"         : "push_horizontal",
    "Incline Dumbbell Press"       : "push_horizontal",
    "Chest Dip"                    : "push_horizontal",
    "Incline Chest Press"          : "push_horizontal",
    # Back
    "Barbell Row"                  : "pull_horizontal",
    "Dumbbell Row"                 : "pull_horizontal",
    "Pull Up"                      : "pull_vertical",
    "Lat Pulldown"                 : "pull_vertical",
    "Seated Cable Row"             : "pull_horizontal",
    "Weighted Pull Up"             : "pull_vertical",
    "Pendlay Row"                  : "pull_horizontal",
    "Horizontal Row"               : "pull_horizontal",
    "Braced Dumbbell Row"          : "pull_horizontal",
    "Close Grip Pulldown"          : "pull_vertical",
    "Hyperextension"               : "hinge",
    # Shoulders
    "Overhead Press"               : "push_vertical",
    "Dumbbell Shoulder Press"      : "push_vertical",
    "Face Pull"                    : "pull_horizontal",
    "Upright Row"                  : "pull_vertical",
    "Barbell Shrug"                : "isolation",
    # Triceps
    "Weighted Dip"                 : "push_horizontal",
}

EXERCISES_TO_DELETE = [
    # "Calf Raise",
    # "DB Side Lateral Raise",
]


def migrate():
    init_db()
    db = SessionLocal()

    updated, skipped, deleted = 0, 0, 0

    # --- Update movement patterns ---
    for name, new_pattern in MOVEMENT_PATTERN_UPDATES.items():
        ex = db.query(Exercise).filter_by(name=name).first()
        if not ex:
            print(f"  NOT FOUND — {name}")
            skipped += 1
            continue
        if ex.movement_pattern == new_pattern:
            skipped += 1
            continue
        print(f"  {name}: {ex.movement_pattern} → {new_pattern}")
        ex.movement_pattern = new_pattern
        updated += 1

    # --- Delete duplicates ---
    for name in EXERCISES_TO_DELETE:
        ex = db.query(Exercise).filter_by(name=name).first()
        if not ex:
            print(f"  NOT FOUND (delete skipped) — {name}")
            continue
        print(f"  DELETING — {name}")
        db.delete(ex)
        deleted += 1

    db.commit()
    db.close()
    print(f"\nDone — {updated} updated, {deleted} deleted, {skipped} skipped.")


if __name__ == "__main__":
    migrate()