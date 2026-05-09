import pandas as pd
from db import SessionLocal, Program, ProgramDay, ProgramSet, Exercise, ExerciseAlias


def import_program(filepath: str, program_name: str, source: str = None):
    """
    Import a program from a flat Excel template into the database.

    Expected columns:
        week, day_num, day_label, exercise_name, set_num,
        target_reps, target_rir, target_pct_1rm, notes
    """
    # -----------------------------------------------------------------------
    # 1. Read the spreadsheet
    # -----------------------------------------------------------------------
    try:
        df = pd.read_excel(filepath, engine="openpyxl")
    except FileNotFoundError:
        print(f"ERROR: File not found — {filepath}")
        return
    except Exception as e:
        print(f"ERROR reading file: {e}")
        return

    # Normalize column names — strip whitespace, lowercase
    df.columns = [c.strip().lower() for c in df.columns]

    required_cols = {
        "week", "day_num", "day_label", "exercise_name",
        "set_num", "target_reps", "target_rir", "target_pct_1rm", "notes"
    }
    missing = required_cols - set(df.columns)
    if missing:
        print(f"ERROR: Missing columns in spreadsheet: {missing}")
        return

    # -----------------------------------------------------------------------
    # 2. Build exercise lookup — canonical names + aliases
    # -----------------------------------------------------------------------
    db = SessionLocal()

    all_exercises = db.query(Exercise).all()

    # Primary map: canonical name (lowercase) -> Exercise
    exercise_map = {ex.name.lower(): ex for ex in all_exercises}

    # Alias map: alias (lowercase) -> Exercise
    all_aliases = db.query(ExerciseAlias).all()
    alias_map = {a.alias.lower(): a.exercise for a in all_aliases}

    def resolve_exercise(name: str):
        """Resolve an exercise name via canonical match first, then alias."""
        key = name.strip().lower()
        return exercise_map.get(key) or alias_map.get(key)

    # Validate all names upfront — report anything unresolvable
    import_names = df["exercise_name"].dropna().unique()
    unmatched = [name for name in import_names if resolve_exercise(name) is None]

    if unmatched:
        print("\nWARNING: The following exercise names couldn't be resolved:")
        for name in unmatched:
            print(f"  - {name}")
        print("\nOptions:")
        print("  1. Fix the name in your spreadsheet to match a canonical name")
        print("  2. Add an alias via seed_aliases.py and re-run")
        print("  3. Run 'python list_exercises.py' to see all valid names.\n")
        db.close()
        return

    # -----------------------------------------------------------------------
    # 3. Check for duplicate program name
    # -----------------------------------------------------------------------
    existing = db.query(Program).filter_by(name=program_name).first()
    if existing:
        print(f"ERROR: A program named '{program_name}' already exists.")
        print("Delete it first or use a different name.")
        db.close()
        return

    # -----------------------------------------------------------------------
    # 4. Create Program row
    # -----------------------------------------------------------------------
    program = Program(name=program_name, source=source)
    db.add(program)
    db.commit()
    db.refresh(program)

    # -----------------------------------------------------------------------
    # 5. Iterate rows — build ProgramDay and ProgramSet rows
    # -----------------------------------------------------------------------
    day_cache = {}
    sets_added = 0
    resolved_via_alias = 0

    for _, row in df.iterrows():
        week      = int(row["week"])
        day_num   = int(row["day_num"])
        day_label = str(row["day_label"]).strip()
        ex_name   = str(row["exercise_name"]).strip()
        set_num   = int(row["set_num"])

        target_reps = (
            None if pd.isna(row["target_reps"])
            else int(row["target_reps"])
        )
        target_rir = (
            None if pd.isna(row["target_rir"])
            else int(row["target_rir"])
        )
        target_pct_1rm = (
            None if pd.isna(row["target_pct_1rm"])
            else float(row["target_pct_1rm"])
        )
        notes = (
            None if pd.isna(row["notes"])
            else str(row["notes"]).strip()
        )

        # Resolve exercise — canonical or alias
        exercise = resolve_exercise(ex_name)
        if ex_name.strip().lower() not in exercise_map:
            resolved_via_alias += 1

        # Get or create ProgramDay
        day_key = (week, day_num)
        if day_key not in day_cache:
            day = ProgramDay(
                program_id=program.id,
                week_num=week,
                day_num=day_num,
                label=day_label,
            )
            db.add(day)
            db.commit()
            db.refresh(day)
            day_cache[day_key] = day.id

        program_set = ProgramSet(
            day_id=day_cache[day_key],
            exercise_id=exercise.id,
            set_num=set_num,
            target_reps=target_reps,
            target_rir=target_rir,
            target_pct_1rm=target_pct_1rm,
            notes=notes,
        )
        db.add(program_set)
        sets_added += 1

    db.commit()
    db.close()

    print(f"\nImport complete.")
    print(f"  Program          : {program_name}")
    print(f"  Weeks            : {df['week'].nunique()}")
    print(f"  Days             : {len(day_cache)}")
    print(f"  Sets             : {sets_added}")
    print(f"  Resolved via alias: {resolved_via_alias}")


# ---------------------------------------------------------------------------
# Run directly: python importer.py
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import_program(
        filepath="phat_import.xlsx",
        program_name="PHAT",
        source="Liftvault - PHAT by Layne Norton",
    )