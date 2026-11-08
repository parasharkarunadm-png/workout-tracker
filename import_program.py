#!/usr/bin/env python3
import argparse
import sys
from typing import Optional

import pandas as pd

from db import Exercise, ExerciseAlias, Program, ProgramDay, ProgramSet, SessionLocal, init_db

REQUIRED_COLUMNS = {
    "week",
    "day_num",
    "day_label",
    "exercise_name",
    "set_num",
    "target_reps",
    "target_rir",
    "target_pct_1rm",
    "notes",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import a CSV program into the workout tracker database."
    )
    parser.add_argument("program_name", help="Name to store for the imported program")
    parser.add_argument("csv_path", help="Path to the CSV file to import")
    parser.add_argument(
        "--source",
        default=None,
        help="Optional source label for the imported program",
    )
    return parser.parse_args()


def normalize_value(value):
    if pd.isna(value):
        return None
    if isinstance(value, str):
        text = value.strip()
        return None if text == "" else text
    return value


def parse_optional_int(value):
    if pd.isna(value):
        return None
    if isinstance(value, str):
        text = value.strip()
        if text == "":
            return None
        return int(float(text))
    return int(value)


def parse_optional_float(value):
    if pd.isna(value):
        return None
    if isinstance(value, str):
        text = value.strip()
        if text == "":
            return None
        return float(text)
    return float(value)


def parse_required_int(value, column_name: str) -> int:
    if pd.isna(value):
        raise ValueError(f"Missing required value for column '{column_name}'")
    if isinstance(value, str):
        text = value.strip()
        if text == "":
            raise ValueError(f"Missing required value for column '{column_name}'")
        return int(float(text))
    return int(value)


def main() -> int:
    args = parse_args()

    try:
        init_db()
        db = SessionLocal()
    except Exception as exc:
        print(f"Database connection failed: {exc}")
        return 1

    try:
        existing_program = (
            db.query(Program).filter(Program.name == args.program_name).first()
        )
        if existing_program is not None:
            print(f"Program '{args.program_name}' already exists. Aborting.")
            return 1

        try:
            df = pd.read_csv(args.csv_path)
        except FileNotFoundError:
            print(f"CSV file not found: {args.csv_path}")
            return 1
        except Exception as exc:
            print(f"Unable to read CSV file: {exc}")
            return 1

        df.columns = [str(col).strip().lower() for col in df.columns]

        missing_columns = sorted(REQUIRED_COLUMNS.difference(df.columns))
        if missing_columns:
            print("Missing required columns:")
            for column in missing_columns:
                print(f"  - {column}")
            return 1

        exercises = db.query(Exercise).all()
        exercise_lookup = {exercise.name.lower(): exercise for exercise in exercises}
        aliases = db.query(ExerciseAlias).all()
        alias_lookup = {alias.alias.lower(): alias.exercise for alias in aliases}

        def resolve_exercise(name: str):
            key = str(name).strip().lower()
            if not key:
                return None
            return exercise_lookup.get(key) or alias_lookup.get(key)

        exercise_names = [
            str(name).strip()
            for name in df["exercise_name"].dropna().unique()
            if str(name).strip()
        ]
        missing_exercises = []
        resolved_exercises = {}

        for exercise_name in exercise_names:
            exercise = resolve_exercise(exercise_name)
            if exercise is None:
                missing_exercises.append(exercise_name)
            else:
                resolved_exercises[exercise_name] = exercise

        if missing_exercises:
            print("Missing exercise names found in CSV:")
            for name in sorted(set(missing_exercises)):
                print(f"  - {name}")
            print("Import aborted before any database writes.")
            return 1

        db.rollback()
        with db.begin():
            program = Program(name=args.program_name, source=args.source)
            db.add(program)
            db.flush()
            db.refresh(program)

            day_cache = {}
            days_created = 0
            sets_created = 0

            for _, row in df.iterrows():
                week = parse_required_int(row["week"], "week")
                day_num = parse_required_int(row["day_num"], "day_num")
                set_num = parse_required_int(row["set_num"], "set_num")
                day_label = normalize_value(row["day_label"])

                day_key = (week, day_num, day_label)
                if day_key not in day_cache:
                    program_day = ProgramDay(
                        program_id=program.id,
                        week_num=week,
                        day_num=day_num,
                        label=day_label,
                    )
                    db.add(program_day)
                    db.flush()
                    day_cache[day_key] = program_day.id
                    days_created += 1

                exercise_name = str(row["exercise_name"]).strip()
                exercise = resolved_exercises[exercise_name]
                program_set = ProgramSet(
                    day_id=day_cache[day_key],
                    exercise_id=exercise.id,
                    set_num=set_num,
                    target_reps=parse_optional_int(row["target_reps"]),
                    target_rir=parse_optional_int(row["target_rir"]),
                    target_pct_1rm=parse_optional_float(row["target_pct_1rm"]),
                    notes=normalize_value(row["notes"]),
                )
                db.add(program_set)
                sets_created += 1

        print("Import complete.")
        print(f"  Program: {args.program_name}")
        print(f"  Days created: {days_created}")
        print(f"  Sets created: {sets_created}")
        return 0

    except Exception as exc:
        db.rollback()
        print(f"Import failed: {exc}")
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
