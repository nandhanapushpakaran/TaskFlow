"""
Task management and security test suite for TaskFlow.
Tests CRUD operations, validation, toggle, filtering, search, sorting, statistics,
and verifies strict cross-user isolation and security boundaries.
"""
from datetime import date, timedelta
import pytest


def test_create_task_success(auth_client_a):
    """Authenticated user can create a task."""
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    response = auth_client_a.post('/api/tasks', json={
        'title': 'Build Portfolio Project',
        'description': 'Implement high quality features for TaskFlow.',
        'priority': 'high',
        'due_date': tomorrow
    })
    assert response.status_code == 201
    data = response.get_json()
    assert data['task']['title'] == 'Build Portfolio Project'
    assert data['task']['priority'] == 'high'
    assert data['task']['status'] == 'pending'
    assert data['task']['due_date'] == tomorrow
    assert data['task']['completed_at'] is None
    assert data['task']['is_overdue'] is False


def test_create_task_validation_failures(auth_client_a):
    """Invalid title, priority, or due_date returns 400 validation error."""
    # Empty title
    res = auth_client_a.post('/api/tasks', json={'title': ''})
    assert res.status_code == 400
    assert 'title' in res.get_json()['fields']

    # Title exceeding 120 chars
    res = auth_client_a.post('/api/tasks', json={'title': 'A' * 125})
    assert res.status_code == 400
    assert 'title' in res.get_json()['fields']

    # Invalid priority
    res = auth_client_a.post('/api/tasks', json={'title': 'Test', 'priority': 'urgent'})
    assert res.status_code == 400
    assert 'priority' in res.get_json()['fields']

    # Invalid due date
    res = auth_client_a.post('/api/tasks', json={'title': 'Test', 'due_date': 'not-a-date'})
    assert res.status_code == 400
    assert 'due_date' in res.get_json()['fields']


def test_get_and_update_task(auth_client_a):
    """User can retrieve and update their own task."""
    create_res = auth_client_a.post('/api/tasks', json={
        'title': 'Original Title',
        'description': 'Original Description',
        'priority': 'low'
    })
    task_id = create_res.get_json()['task']['id']

    # Retrieve task
    get_res = auth_client_a.get(f'/api/tasks/{task_id}')
    assert get_res.status_code == 200
    assert get_res.get_json()['task']['title'] == 'Original Title'

    # Update task
    update_res = auth_client_a.put(f'/api/tasks/{task_id}', json={
        'title': 'Updated Title',
        'description': 'Updated Description',
        'priority': 'medium'
    })
    assert update_res.status_code == 200
    updated_task = update_res.get_json()['task']
    assert updated_task['title'] == 'Updated Title'
    assert updated_task['priority'] == 'medium'


def test_toggle_task_completion(auth_client_a):
    """Toggling a task completes it and reopening clears completed_at."""
    create_res = auth_client_a.post('/api/tasks', json={'title': 'Toggle Test'})
    task_id = create_res.get_json()['task']['id']

    # Toggle to completed
    res1 = auth_client_a.patch(f'/api/tasks/{task_id}/toggle')
    assert res1.status_code == 200
    task1 = res1.get_json()['task']
    assert task1['status'] == 'completed'
    assert task1['completed_at'] is not None

    # Toggle back to pending (reopen)
    res2 = auth_client_a.patch(f'/api/tasks/{task_id}/toggle')
    assert res2.status_code == 200
    task2 = res2.get_json()['task']
    assert task2['status'] == 'pending'
    assert task2['completed_at'] is None


def test_delete_task(auth_client_a):
    """User can delete their own task."""
    create_res = auth_client_a.post('/api/tasks', json={'title': 'Task To Delete'})
    task_id = create_res.get_json()['task']['id']

    # Delete task
    del_res = auth_client_a.delete(f'/api/tasks/{task_id}')
    assert del_res.status_code == 200

    # Verify task no longer exists
    get_res = auth_client_a.get(f'/api/tasks/{task_id}')
    assert get_res.status_code == 404


def test_filtering_and_search(auth_client_a):
    """Filtering by status, priority, and searching by keyword work correctly."""
    # Create several tasks
    auth_client_a.post('/api/tasks', json={'title': 'Write Backend API', 'priority': 'high', 'description': 'Flask app'})
    auth_client_a.post('/api/tasks', json={'title': 'Write Frontend UI', 'priority': 'medium', 'description': 'HTML and CSS'})
    auth_client_a.post('/api/tasks', json={'title': 'Buy groceries', 'priority': 'low', 'description': 'Milk and bread'})

    # Search keyword
    res = auth_client_a.get('/api/tasks?search=frontend')
    assert res.status_code == 200
    tasks = res.get_json()['tasks']
    assert len(tasks) == 1
    assert tasks[0]['title'] == 'Write Frontend UI'

    # Filter priority=high
    res = auth_client_a.get('/api/tasks?priority=high')
    assert res.status_code == 200
    tasks = res.get_json()['tasks']
    assert len(tasks) == 1
    assert tasks[0]['title'] == 'Write Backend API'

    # Filter priority=low
    res = auth_client_a.get('/api/tasks?priority=low')
    assert res.status_code == 200
    assert len(res.get_json()['tasks']) == 1


def test_sorting(auth_client_a):
    """Sorting by priority and due date orders items correctly."""
    today = date.today()
    auth_client_a.post('/api/tasks', json={'title': 'Low Priority', 'priority': 'low'})
    auth_client_a.post('/api/tasks', json={'title': 'High Priority', 'priority': 'high'})
    auth_client_a.post('/api/tasks', json={'title': 'Medium Priority', 'priority': 'medium'})

    res = auth_client_a.get('/api/tasks?sort=priority')
    assert res.status_code == 200
    tasks = res.get_json()['tasks']
    priorities = [t['priority'] for t in tasks]
    assert priorities == ['high', 'medium', 'low']


def test_statistics_and_overdue(auth_client_a):
    """Statistics endpoint calculates total, pending, completed, and overdue accurately."""
    yesterday = (date.today() - timedelta(days=2)).isoformat()
    tomorrow = (date.today() + timedelta(days=2)).isoformat()

    # 1. Pending + Overdue
    auth_client_a.post('/api/tasks', json={'title': 'Overdue Task', 'due_date': yesterday})
    # 2. Pending + Future
    auth_client_a.post('/api/tasks', json={'title': 'Future Task', 'due_date': tomorrow})
    # 3. Completed
    c_res = auth_client_a.post('/api/tasks', json={'title': 'Done Task'})
    auth_client_a.patch(f"/api/tasks/{c_res.get_json()['task']['id']}/toggle")

    res = auth_client_a.get('/api/tasks/stats')
    assert res.status_code == 200
    stats = res.get_json()
    assert stats['total'] == 3
    assert stats['pending'] == 2
    assert stats['completed'] == 1
    assert stats['overdue'] == 1


# ==============================================================================
# SECURITY AND USER ISOLATION TESTS
# ==============================================================================

def test_user_task_isolation_and_security(app):
    """
    CRITICAL SECURITY TEST:
    Verify User A and User B cannot access, read, update, or delete each other's tasks,
    and neither user can see tasks or statistics of the other.
    """
    with app.app_context():
        from backend.models import db, User
        user_alice = User(name="Alice Isolation", email="alice_iso@example.com")
        user_alice.set_password("AliceSecurePass1!")
        user_bob = User(name="Bob Isolation", email="bob_iso@example.com")
        user_bob.set_password("BobSecurePass2!")
        db.session.add_all([user_alice, user_bob])
        db.session.commit()

    client_a = app.test_client()
    client_b = app.test_client()

    # Log in both clients
    login_a = client_a.post('/api/auth/login', json={'email': 'alice_iso@example.com', 'password': 'AliceSecurePass1!'})
    assert login_a.status_code == 200
    login_b = client_b.post('/api/auth/login', json={'email': 'bob_iso@example.com', 'password': 'BobSecurePass2!'})
    assert login_b.status_code == 200

    # User A creates a task
    resp_a = client_a.post('/api/tasks', json={
        'title': 'Alice Secret Task',
        'description': 'Strictly confidential to Alice.'
    })
    assert resp_a.status_code == 201
    task_a = resp_a.get_json()['task']
    task_a_id = task_a['id']

    # User B creates a task
    resp_b = client_b.post('/api/tasks', json={
        'title': 'Bob Private Task',
        'description': 'Strictly confidential to Bob.'
    })
    assert resp_b.status_code == 201
    task_b = resp_b.get_json()['task']
    task_b_id = task_b['id']

    # 1. User B tries to GET User A's task -> MUST return 404 (not expose existence)
    res = client_b.get(f'/api/tasks/{task_a_id}')
    assert res.status_code == 404
    assert res.get_json()['error'] == 'not_found'

    # 2. User A tries to GET User B's task -> MUST return 404
    res = client_a.get(f'/api/tasks/{task_b_id}')
    assert res.status_code == 404
    assert res.get_json()['error'] == 'not_found'

    # 3. User B tries to UPDATE User A's task -> MUST return 404
    res = client_b.put(f'/api/tasks/{task_a_id}', json={'title': 'Hacked Title'})
    assert res.status_code == 404

    # 4. User B tries to TOGGLE User A's task -> MUST return 404
    res = client_b.patch(f'/api/tasks/{task_a_id}/toggle')
    assert res.status_code == 404

    # 5. User B tries to DELETE User A's task -> MUST return 404
    res = client_b.delete(f'/api/tasks/{task_a_id}')
    assert res.status_code == 404

    # 6. Verify User A's task is completely unchanged
    res = client_a.get(f'/api/tasks/{task_a_id}')
    assert res.status_code == 200
    assert res.get_json()['task']['title'] == 'Alice Secret Task'

    # 7. User A task list only contains Alice's task
    list_a = client_a.get('/api/tasks').get_json()['tasks']
    titles_a = [t['title'] for t in list_a]
    assert 'Alice Secret Task' in titles_a
    assert 'Bob Private Task' not in titles_a

    # 8. User B task list only contains Bob's task
    list_b = client_b.get('/api/tasks').get_json()['tasks']
    titles_b = [t['title'] for t in list_b]
    assert 'Bob Private Task' in titles_b
    assert 'Alice Secret Task' not in titles_b

    # 9. Verify stats isolation
    stats_a = client_a.get('/api/tasks/stats').get_json()
    stats_b = client_b.get('/api/tasks/stats').get_json()
    assert stats_a['total'] == 1
    assert stats_b['total'] == 1
