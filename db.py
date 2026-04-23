from sqlalchemy import (
    create_engine, Column, Integer, String, Float,
    Boolean, DateTime, ForeignKey, Text
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime

Base = declarative_base()


# ---------------------------------------------------------------------------
# Layer 1 — Reference data
# ---------------------------------------------------------------------------

class Exercise(Base):
    __tablename__ = "exercises"

    id               = Column(Integer, primary_key=True)
    name             = Column(String, nullable=False, unique=True)
    primary_muscle   = Column(String, nullable=False)   # e.g. "chest", "back"
    equipment        = Column(String, nullable=False)   # e.g. "barbell", "dumbbell"
    movement_pattern = Column(String, nullable=False)   # e.g. "push", "pull", "hinge"
    notes            = Column(Text, nullable=True)      # optional form cues

    program_sets = relationship("ProgramSet", back_populates="exercise")
    logged_sets  = relationship("LoggedSet",  back_populates="exercise")


# ---------------------------------------------------------------------------
# Layer 2 — Program structure
# ---------------------------------------------------------------------------

class Program(Base):
    __tablename__ = "programs"

    id         = Column(Integer, primary_key=True)
    name       = Column(String, nullable=False)
    source     = Column(String, nullable=True)   # e.g. "Liftvault - Reddit PPL"
    created_at = Column(DateTime, default=datetime.utcnow)

    days = relationship("ProgramDay", back_populates="program")


class ProgramDay(Base):
    __tablename__ = "program_days"

    id        = Column(Integer, primary_key=True)
    program_id = Column(Integer, ForeignKey("programs.id"), nullable=False)
    week_num  = Column(Integer, nullable=False)   # 1-indexed
    day_num   = Column(Integer, nullable=False)   # 1-indexed within week
    label     = Column(String, nullable=True)     # e.g. "Push A", "Legs"

    program  = relationship("Program",     back_populates="days")
    sets     = relationship("ProgramSet",  back_populates="day")
    sessions = relationship("Session",     back_populates="program_day")


class ProgramSet(Base):
    __tablename__ = "program_sets"

    id             = Column(Integer, primary_key=True)
    day_id         = Column(Integer, ForeignKey("program_days.id"), nullable=False)
    exercise_id    = Column(Integer, ForeignKey("exercises.id"),    nullable=False)
    set_num        = Column(Integer, nullable=False)   # order within the day
    target_reps    = Column(Integer, nullable=True)    # null = AMRAP
    target_rir     = Column(Integer, nullable=True)    # null = not specified
    notes          = Column(Text,    nullable=True)    # e.g. "pause at bottom"

    day      = relationship("ProgramDay", back_populates="sets")
    exercise = relationship("Exercise",   back_populates="program_sets")


# ---------------------------------------------------------------------------
# Layer 3 — Actual logging
# ---------------------------------------------------------------------------

class Session(Base):
    __tablename__ = "sessions"

    id             = Column(Integer, primary_key=True)
    program_day_id = Column(Integer, ForeignKey("program_days.id"), nullable=False)
    date           = Column(DateTime, default=datetime.utcnow)
    duration_mins  = Column(Integer, nullable=True)   # filled on session close
    notes          = Column(Text,    nullable=True)

    program_day = relationship("ProgramDay", back_populates="sessions")
    logged_sets = relationship("LoggedSet",  back_populates="session")


class LoggedSet(Base):
    __tablename__ = "logged_sets"

    id             = Column(Integer, primary_key=True)
    session_id     = Column(Integer, ForeignKey("sessions.id"),    nullable=False)
    exercise_id    = Column(Integer, ForeignKey("exercises.id"),   nullable=False)
    program_set_id = Column(Integer, ForeignKey("program_sets.id"), nullable=True)  # null = ad-hoc
    set_num        = Column(Integer, nullable=False)
    weight_lb      = Column(Float,   nullable=False)
    reps           = Column(Integer, nullable=False)
    rir            = Column(Integer, nullable=True)    # reps in reserve
    rest_secs      = Column(Integer, nullable=True)    # seconds since last set
    # weight stored in kg throughout — no unit conversion needed
    is_pr          = Column(Boolean, default=False)
    set_type       = Column(String,  default="working")  # working / warmup / failure / drop
    logged_at      = Column(DateTime, default=datetime.utcnow)

    session     = relationship("Session",    back_populates="logged_sets")
    exercise    = relationship("Exercise",   back_populates="logged_sets")


# ---------------------------------------------------------------------------
# Engine + session factory
# ---------------------------------------------------------------------------

engine = create_engine("sqlite:///workout.db", echo=False)

SessionLocal = sessionmaker(bind=engine)


def init_db():
    """Call once on app startup to create all tables if they don't exist."""
    Base.metadata.create_all(engine)


def get_db():
    """Use as a context manager: with get_db() as db: ..."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()