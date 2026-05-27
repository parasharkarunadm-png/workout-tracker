from db import SessionLocal, Program, ProgramDay

db = SessionLocal()
prog = db.query(Program).filter(Program.name.ilike('%dorian%')).first()
if prog:
    for day in sorted(prog.days, key=lambda d: (d.week_num, d.day_num)):
        print(f'Week {day.week_num} Day {day.day_num}: {day.label}')
else:
    print('Program not found')
db.close()