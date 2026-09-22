"""
Demo data seeder for TaskFlow.
Usage: python seed.py
Creates a demo user: demo@taskflow.dev (password: TaskFlow2026!) with starter tasks.
"""
from datetime import date, timedelta, datetime
from backend import create_app
from backend.models import db, User, Task

app = create_app()

DEMO_USER_EMAIL = "demo@taskflow.dev"
DEMO_USER_PASSWORD = "TaskFlow2026!"
DEMO_USER_NAME = "Alex Developer"

DEMO_TASKS = [
    {
        "title": "Prepare portfolio README",
        "description": "Add screenshots, architecture overview, and setup instructions to showcase TaskFlow.",
        "priority": "high",
        "status": "pending",
        "due_date_offset": 2,  # 2 days from now
    },
    {
        "title": "Practice Flask API routes",
        "description": "Verify RESTful standards, route blueprints, error handling, and test coverage.",
        "priority": "medium",
        "status": "completed",
        "due_date_offset": -1,  # yesterday
        "completed": True,
    },
    {
        "title": "Review JavaScript fetch()",
        "description": "Ensure error handling, loading states, and state updates work smoothly in vanilla JS.",
        "priority": "medium",
        "status": "pending",
        "due_date_offset": 5,  # 5 days from now
    },
    {
        "title": "Clean GitHub repository",
        "description": "Double check .gitignore, remove unused temp files, and ensure clean Git history.",
        "priority": "low",
        "status": "pending",
        "due_date_offset": 7,  # 7 days from now
    },
    {
        "title": "Update project documentation",
        "description": "Complete code comments, accessibility notes, and keyboard navigation testing.",
        "priority": "high",
        "status": "pending",
        "due_date_offset": -2,  # Overdue task to demonstrate overdue highlighting!
    },
]


def seed():
    with app.app_context():
        print("[*] Seeding TaskFlow database...")

        # Check or create demo user
        user = User.query.filter_by(email=DEMO_USER_EMAIL).first()
        if not user:
            user = User(name=DEMO_USER_NAME, email=DEMO_USER_EMAIL)
            user.set_password(DEMO_USER_PASSWORD)
            db.session.add(user)
            db.session.commit()
            print(f"Created demo user: {DEMO_USER_EMAIL}")
        else:
            print(f"Demo user already exists: {DEMO_USER_EMAIL}")

        # Clear existing demo tasks to allow clean re-seeding
        Task.query.filter_by(user_id=user.id).delete()
        db.session.commit()

        today = date.today()
        for task_info in DEMO_TASKS:
            due = today + timedelta(days=task_info["due_date_offset"])
            status = task_info["status"]
            completed_at = datetime.utcnow() if status == "completed" else None

            task = Task(
                user_id=user.id,
                title=task_info["title"],
                description=task_info["description"],
                priority=task_info["priority"],
                status=status,
                due_date=due,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                completed_at=completed_at,
            )
            db.session.add(task)

        db.session.commit()
        print(f"[OK] Successfully seeded {len(DEMO_TASKS)} demo tasks for {DEMO_USER_EMAIL}")
        print(f"   Login with:")
        print(f"   Email:    {DEMO_USER_EMAIL}")
        print(f"   Password: {DEMO_USER_PASSWORD}")


if __name__ == "__main__":
    seed()
