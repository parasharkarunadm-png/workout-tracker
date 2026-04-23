from db import SessionLocal, Exercise

db = SessionLocal()
exercises = db.query(Exercise).order_by(Exercise.primary_muscle, Exercise.name).all()
db.close()

print(f"\n{'Muscle':<15} {'Equipment':<12} {'Pattern':<12} Name")
print("-" * 65)
for ex in exercises:
    print(f"{ex.primary_muscle:<15} {ex.equipment:<12} {ex.movement_pattern:<12} {ex.name}")