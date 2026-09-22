"""
Validation and utility helpers for TaskFlow.
Provides input validation, date parsing, and standard JSON response formatters.
"""
import re
from datetime import datetime, date
from typing import Tuple, Dict, Any, Optional

# Basic RFC 5322 compliant regex for email validation
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

VALID_PRIORITIES = {'low', 'medium', 'high'}
VALID_STATUSES = {'pending', 'completed'}


def validate_registration_data(data: Optional[Dict[str, Any]]) -> Tuple[bool, Dict[str, str], Dict[str, str]]:
    """
    Validate user registration payload.
    Requirements:
    - Name: 2-80 characters
    - Email: Valid format, normalized with strip().lower()
    - Password: Min 8 characters
    - Confirm Password: Must match password if provided
    """
    if not data or not isinstance(data, dict):
        return False, {"general": "Request body must be a JSON object."}, {}

    errors = {}
    cleaned = {}

    # Validate Name
    raw_name = data.get('name')
    if not raw_name or not isinstance(raw_name, str):
        errors['name'] = "Name is required."
    else:
        name = raw_name.strip()
        if len(name) < 2 or len(name) > 80:
            errors['name'] = "Name must be between 2 and 80 characters."
        else:
            cleaned['name'] = name

    # Validate Email
    raw_email = data.get('email')
    if not raw_email or not isinstance(raw_email, str):
        errors['email'] = "Email is required."
    else:
        email = raw_email.strip().lower()
        if not EMAIL_REGEX.match(email):
            errors['email'] = "Please provide a valid email address."
        else:
            cleaned['email'] = email

    # Validate Password
    password = data.get('password')
    if not password or not isinstance(password, str):
        errors['password'] = "Password is required."
    elif len(password) < 8:
        errors['password'] = "Password must be at least 8 characters long."
    else:
        cleaned['password'] = password

    # Validate Confirm Password
    confirm_password = data.get('confirm_password')
    if confirm_password is not None and confirm_password != password:
        errors['confirm_password'] = "Passwords do not match."

    return len(errors) == 0, errors, cleaned


def validate_task_data(data: Optional[Dict[str, Any]], is_update: bool = False) -> Tuple[bool, Dict[str, str], Dict[str, Any]]:
    """
    Validate task creation or update payload.
    Requirements:
    - Title: 1-120 characters, required
    - Description: Optional, max 1000 characters
    - Priority: 'low', 'medium', or 'high' (default: 'medium')
    - Status: 'pending' or 'completed' (default: 'pending')
    - Due Date: Optional valid date format (YYYY-MM-DD)
    """
    if not data or not isinstance(data, dict):
        return False, {"general": "Request body must be a JSON object."}, {}

    errors = {}
    cleaned = {}

    # Validate Title
    if 'title' in data or not is_update:
        raw_title = data.get('title')
        if not raw_title or not isinstance(raw_title, str) or not raw_title.strip():
            errors['title'] = "Title is required (1-120 characters)."
        else:
            title = raw_title.strip()
            if len(title) > 120:
                errors['title'] = "Title must be 120 characters or fewer."
            else:
                cleaned['title'] = title

    # Validate Description
    if 'description' in data:
        raw_desc = data.get('description')
        if raw_desc is None or raw_desc == "":
            cleaned['description'] = ""
        elif isinstance(raw_desc, str):
            if len(raw_desc) > 1000:
                errors['description'] = "Description must not exceed 1000 characters."
            else:
                cleaned['description'] = raw_desc.strip()
        else:
            errors['description'] = "Description must be a string."
    elif not is_update:
        cleaned['description'] = ""

    # Validate Priority
    if 'priority' in data:
        raw_priority = data.get('priority')
        if not raw_priority or raw_priority.lower() not in VALID_PRIORITIES:
            errors['priority'] = f"Priority must be one of: {', '.join(sorted(VALID_PRIORITIES))}."
        else:
            cleaned['priority'] = raw_priority.lower()
    elif not is_update:
        cleaned['priority'] = 'medium'

    # Validate Status
    if 'status' in data:
        raw_status = data.get('status')
        if not raw_status or raw_status.lower() not in VALID_STATUSES:
            errors['status'] = f"Status must be one of: {', '.join(sorted(VALID_STATUSES))}."
        else:
            cleaned['status'] = raw_status.lower()
    elif not is_update:
        cleaned['status'] = 'pending'

    # Validate Due Date
    if 'due_date' in data:
        raw_due_date = data.get('due_date')
        if raw_due_date in (None, ""):
            cleaned['due_date'] = None
        elif isinstance(raw_due_date, str):
            try:
                cleaned['due_date'] = datetime.strptime(raw_due_date.strip()[:10], "%Y-%m-%d").date()
            except ValueError:
                errors['due_date'] = "Due date must be in YYYY-MM-DD format."
        elif isinstance(raw_due_date, (date, datetime)):
            cleaned['due_date'] = raw_due_date if isinstance(raw_due_date, date) else raw_due_date.date()
        else:
            errors['due_date'] = "Due date must be a valid date string."
    elif not is_update:
        cleaned['due_date'] = None

    return len(errors) == 0, errors, cleaned


def validation_error_response(errors: Dict[str, str]):
    """Standardized validation error JSON structure."""
    return {
        "error": "validation_error",
        "message": "Please correct the highlighted fields.",
        "fields": errors
    }, 400
