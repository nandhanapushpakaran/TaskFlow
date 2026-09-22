"""
Task management endpoints for TaskFlow.
Implements full CRUD, toggle, statistics, filtering, searching, and sorting.
All operations strictly enforce user task ownership via Flask-Login session.
"""
from datetime import datetime, date
from flask import request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import case, or_
from backend.models import db, Task
from backend.utils import validate_task_data, validation_error_response
from . import tasks_bp


@tasks_bp.route('', methods=['GET'])
@login_required
def list_tasks():
    """
    List tasks belonging to the current user with optional filtering, search, and sorting.
    Query parameters:
    - status: 'pending', 'completed', or 'all'
    - priority: 'low', 'medium', 'high', or 'all'
    - search: search keyword across title and description
    - sort: 'created_desc', 'created_asc', 'due_date', 'priority'
    """
    query = Task.query.filter(Task.user_id == current_user.id)

    # Status filter
    status = request.args.get('status', '').strip().lower()
    if status in ('pending', 'completed'):
        query = query.filter(Task.status == status)

    # Priority filter
    priority = request.args.get('priority', '').strip().lower()
    if priority in ('low', 'medium', 'high'):
        query = query.filter(Task.priority == priority)

    # Search filter
    search = request.args.get('search', '').strip()
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Task.title.ilike(search_pattern),
                Task.description.ilike(search_pattern)
            )
        )

    # Sorting
    sort = request.args.get('sort', 'created_desc').strip().lower()
    if sort == 'created_asc':
        query = query.order_by(Task.created_at.asc())
    elif sort == 'due_date':
        # Tasks with due date first (ascending), tasks without due date placed last
        query = query.order_by(
            case((Task.due_date.is_(None), 1), else_=0).asc(),
            Task.due_date.asc(),
            Task.created_at.desc()
        )
    elif sort == 'priority':
        # Order: High (1) -> Medium (2) -> Low (3)
        priority_order = case(
            (Task.priority == 'high', 1),
            (Task.priority == 'medium', 2),
            (Task.priority == 'low', 3),
            else_=4
        )
        query = query.order_by(priority_order.asc(), Task.created_at.desc())
    else:
        # Default: newest first
        query = query.order_by(Task.created_at.desc())

    tasks = query.all()
    return jsonify({
        'tasks': [task.to_dict() for task in tasks],
        'count': len(tasks)
    }), 200


@tasks_bp.route('', methods=['POST'])
@login_required
def create_task():
    """Create a new task belonging to the current user."""
    data = request.get_json(silent=True)
    is_valid, errors, cleaned = validate_task_data(data, is_update=False)

    if not is_valid:
        return validation_error_response(errors)

    task = Task(
        user_id=current_user.id,
        title=cleaned['title'],
        description=cleaned['description'],
        priority=cleaned['priority'],
        status='pending',
        due_date=cleaned['due_date'],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        completed_at=None
    )

    try:
        db.session.add(task)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({
            'error': 'server_error',
            'message': 'Failed to create task. Please try again.'
        }), 500

    return jsonify({
        'message': 'Task created successfully.',
        'task': task.to_dict()
    }), 201


@tasks_bp.route('/<int:task_id>', methods=['GET'])
@login_required
def get_task(task_id: int):
    """Retrieve a single task strictly belonging to the current user."""
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first()
    if not task:
        return jsonify({
            'error': 'not_found',
            'message': 'Task not found.'
        }), 404

    return jsonify({
        'task': task.to_dict()
    }), 200


@tasks_bp.route('/<int:task_id>', methods=['PUT'])
@login_required
def update_task(task_id: int):
    """Update an existing task strictly belonging to the current user."""
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first()
    if not task:
        return jsonify({
            'error': 'not_found',
            'message': 'Task not found.'
        }), 404

    data = request.get_json(silent=True)
    is_valid, errors, cleaned = validate_task_data(data, is_update=True)

    if not is_valid:
        return validation_error_response(errors)

    if 'title' in cleaned:
        task.title = cleaned['title']
    if 'description' in cleaned:
        task.description = cleaned['description']
    if 'priority' in cleaned:
        task.priority = cleaned['priority']
    if 'due_date' in cleaned:
        task.due_date = cleaned['due_date']
    if 'status' in cleaned:
        new_status = cleaned['status']
        if new_status == 'completed' and task.status != 'completed':
            task.completed_at = datetime.utcnow()
        elif new_status == 'pending' and task.status == 'completed':
            task.completed_at = None
        task.status = new_status

    task.updated_at = datetime.utcnow()

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({
            'error': 'server_error',
            'message': 'Failed to update task. Please try again.'
        }), 500

    return jsonify({
        'message': 'Task updated successfully.',
        'task': task.to_dict()
    }), 200


@tasks_bp.route('/<int:task_id>/toggle', methods=['PATCH'])
@login_required
def toggle_task(task_id: int):
    """Toggle completion status between pending and completed."""
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first()
    if not task:
        return jsonify({
            'error': 'not_found',
            'message': 'Task not found.'
        }), 404

    if task.status == 'pending':
        task.status = 'completed'
        task.completed_at = datetime.utcnow()
        action_msg = 'Task marked as completed.'
    else:
        task.status = 'pending'
        task.completed_at = None
        action_msg = 'Task reopened.'

    task.updated_at = datetime.utcnow()

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({
            'error': 'server_error',
            'message': 'Failed to toggle task. Please try again.'
        }), 500

    return jsonify({
        'message': action_msg,
        'task': task.to_dict()
    }), 200


@tasks_bp.route('/<int:task_id>', methods=['DELETE'])
@login_required
def delete_task(task_id: int):
    """Delete a task strictly belonging to the current user."""
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first()
    if not task:
        return jsonify({
            'error': 'not_found',
            'message': 'Task not found.'
        }), 404

    try:
        db.session.delete(task)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({
            'error': 'server_error',
            'message': 'Failed to delete task. Please try again.'
        }), 500

    return jsonify({
        'message': 'Task deleted successfully.'
    }), 200


@tasks_bp.route('/stats', methods=['GET'])
@login_required
def get_task_stats():
    """Return task counts and statistics for the current user."""
    today = date.today()

    total = Task.query.filter_by(user_id=current_user.id).count()
    pending = Task.query.filter_by(user_id=current_user.id, status='pending').count()
    completed = Task.query.filter_by(user_id=current_user.id, status='completed').count()
    overdue = Task.query.filter(
        Task.user_id == current_user.id,
        Task.status == 'pending',
        Task.due_date.isnot(None),
        Task.due_date < today
    ).count()

    return jsonify({
        'total': total,
        'pending': pending,
        'completed': completed,
        'overdue': overdue
    }), 200
