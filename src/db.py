"""Database setup and models for the Mergington High School activities app."""
from __future__ import annotations

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Boolean,
    ForeignKey,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, Session
from typing import Dict

# SQLite file in workspace (relative path)
DATABASE_URL = "sqlite:///./mhs_activities.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    schedule = Column(String, nullable=True)
    max_participants = Column(Integer, default=0)

    participants = relationship("Participant", back_populates="activity", cascade="all, delete-orphan")


class Participant(Base):
    __tablename__ = "participants"

    id = Column(Integer, primary_key=True)
    email = Column(String, index=True, nullable=False)
    activity_id = Column(Integer, ForeignKey("activities.id"), nullable=False)

    activity = relationship("Activity", back_populates="participants")


def init_db(seed_data: Dict[str, Dict] | None = None) -> None:
    """Create tables and optionally seed with initial data.

    seed_data: mapping of activity name -> {description, schedule, max_participants, participants}
    """
    Base.metadata.create_all(bind=engine)
    if not seed_data:
        return

    with SessionLocal() as db:  # type: Session
        # seed only when no activities exist
        existing = db.query(Activity).count()
        if existing > 0:
            return

        for name, info in seed_data.items():
            act = Activity(
                name=name,
                description=info.get("description"),
                schedule=info.get("schedule"),
                max_participants=info.get("max_participants") or 0,
            )
            db.add(act)
            db.flush()
            # add participants if provided
            for email in info.get("participants", []):
                p = Participant(email=email, activity_id=act.id)
                db.add(p)

        db.commit()


def get_db():
    """Yield a database session; dependency for FastAPI endpoints."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
