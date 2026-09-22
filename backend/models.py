"""
Database models for TaskFlow.
Defines User and Task models with relationships, password hashing, and serialization.
"""
from datetime import datetime, date
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """User account model for authentication and task ownership."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # 1 User -> Many Tasks with cascade deletion
    tasks = db.relationship('Task', back_populates='user', cascade='all, delete-orphan', lazy=True)

    def set_password(self, password: str) -> None:
        """Hash and store user password securely."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verify password against stored Werkzeug hash."""
        return check_password_hash(self.password_hash, password)

    def to_dict(self) -> dict:
        """Safe serialization: NEVER expose password_hash."""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self) -> str:
        return f"<User id={self.id} email='{self.email}'>"


class Task(db.Model):
    """Task item model scoped to an authenticated user."""
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='pending')  # 'pending' or 'completed'
    priority = db.Column(db.String(20), nullable=False, default='medium')  # 'low', 'medium', 'high'
    due_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    completed_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship('User', back_populates='tasks')

    # Index for fast filtering and sorting by user_id and status/priority
    __table_args__ = (
        db.Index('ix_tasks_user_status', 'user_id', 'status'),
        db.Index('ix_tasks_user_priority', 'user_id', 'priority'),
    )

    @property
    def is_overdue(self) -> bool:
        """Returns True if task is pending and due_date has passed."""
        if self.status == 'pending' and self.due_date:
            return self.due_date < date.today()
        return False

    def to_dict(self) -> dict:
        """Serialize task fields for JSON API consumption."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'description': self.description or '',
            'status': self.status,
            'priority': self.priority,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'is_overdue': self.is_overdue
        }

    def __repr__(self) -> str:
        return f"<Task id={self.id} user_id={self.user_id} title='{self.title[:20]}' status='{self.status}'>"
