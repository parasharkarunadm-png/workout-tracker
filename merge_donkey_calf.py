from db import SessionLocal, LoggedSet, Exercise

def merge_donkey_to_standing():
    db = SessionLocal()

    sets = db.query(LoggedSet).filter_by(exercise_id=61).all()
    for s in sets:
        s.exercise_id = 59

    db.commit()
    db.close()
    print(f"Done — {len(sets)} sets migrated from Donkey Calf Raise to Standing Calf Raise.")

if __name__ == "__main__":
    merge_donkey_to_standing()