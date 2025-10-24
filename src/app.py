"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
from pathlib import Path

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# In-memory activity seed (will be migrated into SQLite on startup)
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}
from db import init_db, get_db, Activity, Participant


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.on_event("startup")
def on_startup():
    # initialize sqlite DB and seed from the in-memory dict if DB is empty
    init_db(seed_data=activities)


@app.get("/activities")
def get_activities(db=Depends(get_db)):
    """Return all activities with participant lists."""
    result = {}
    for act in db.query(Activity).all():
        result[act.name] = {
            "description": act.description,
            "schedule": act.schedule,
            "max_participants": act.max_participants,
            "participants": [p.email for p in act.participants],
        }
    return result


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str, db=Depends(get_db)):
    """Sign up a student for an activity (persisted in SQLite)."""
    act = db.query(Activity).filter(Activity.name == activity_name).first()
    if not act:
        raise HTTPException(status_code=404, detail="Activity not found")

    # check already signed up
    existing = db.query(Participant).filter(Participant.activity_id == act.id, Participant.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Student is already signed up")

    # check capacity if set (>0 means limited)
    if act.max_participants and len(act.participants) >= act.max_participants:
        raise HTTPException(status_code=400, detail="Activity is full")

    p = Participant(email=email, activity_id=act.id)
    db.add(p)
    db.commit()
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str, db=Depends(get_db)):
    """Unregister a student from an activity (persisted)."""
    act = db.query(Activity).filter(Activity.name == activity_name).first()
    if not act:
        raise HTTPException(status_code=404, detail="Activity not found")

    p = db.query(Participant).filter(Participant.activity_id == act.id, Participant.email == email).first()
    if not p:
        raise HTTPException(status_code=400, detail="Student is not signed up for this activity")

    db.delete(p)
    db.commit()
    return {"message": f"Unregistered {email} from {activity_name}"}
