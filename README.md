# TaskFlow

> **Organize your work. Clear your mind.**

TaskFlow is a modern, responsive, portfolio-grade personal task management application built with a Python (Flask) REST backend, SQLite / SQLAlchemy persistence, and a modern Vanilla JavaScript frontend.

---

## Overview

Unlike basic CRUD tutorial projects, **TaskFlow** is crafted to feel like a modern SaaS productivity tool. It combines an accessible UI design system, fluid micro-interactions, dark mode, robust session-based authentication, real-time filtering, instant search, and live productivity analytics — all while keeping the architecture simple, transparent, and beginner-friendly.

---

## Core Features

- **Personal Task Management**: Create, read, update, complete/reopen, and delete tasks with smooth client-side interactions.
- **Strict Data Isolation**: Tasks and statistics are strictly scoped to the authenticated session user. Users can never view, mutate, or detect the existence of another user's data.
- **Productivity Analytics**: Real-time statistical cards calculating Total Tasks, Pending, Completed, and Overdue items.
- **Smart Due Dates & Overdue Highlighting**: Clear indicators highlighting tasks that are due today, tomorrow, or overdue by $N$ days.
- **Search, Filter & Sort**:
  - Live 300ms debounced search across titles and descriptions.
  - Filter by Status (`Pending`, `Completed`).
  - Filter by Priority (`Low`, `Medium`, `High`).
  - Sort by Newest first, Oldest first, Due Date, or Priority.
  - Contextual "Clear filters" action.
- **Accessible Modals & Notifications**:
  - Task Creation and Editing in an accessible modal dialog with live 1000-character description counters.
  - Two-step confirmation modal for task deletion.
  - Floating toast notification system with auto-dismiss and manual dismiss.
- **Dark Mode Support**:
  - Genuine dark theme with high contrast and pleasant surface slate colors.
  - Automatically respects system `prefers-color-scheme`.
  - Persists preference in `localStorage`.
- **Responsive Layout**: Designed and verified across mobile viewports (360px–414px), tablets (768px), and desktop displays (1024px–1440px+).
- **Comprehensive Test Suite**: 17 automated pytest test cases covering authentication, task CRUD, input validation, and security boundaries.

---

## Tech Stack

| Layer | Technology | Description |
| :--- | :--- | :--- |
| **Frontend** | HTML5, CSS3, Vanilla JavaScript | Semantic HTML, custom CSS variables design system, fetch API, DOM manipulation (No React/Vue/TypeScript) |
| **Backend** | Python 3, Flask | Application factory pattern, modular Blueprints, JSON REST API |
| **Database** | SQLite, SQLAlchemy / Flask-SQLAlchemy | Relational database with Foreign Keys, indexes, and cascade deletion |
| **Auth** | Flask-Login, Werkzeug | Session-based authentication, secure cookies, Werkzeug scrypt/pbkdf2 password hashing |
| **Security** | python-dotenv, SameSite, HttpOnly | Configurable secure cookies, environment secrets, safe textContent rendering |
| **Testing** | pytest | Automated integration and cross-user security isolation testing |

---

## Architecture

The project maintains a simple and transparent request/response lifecycle:

```
┌────────────────────────────────────────────────────────┐
│                   Browser (Client)                     │
│  - Semantic HTML5, CSS Variables Design System         │
│  - Vanilla JavaScript (Fetch API, DOM manipulation)    │
│  - Safe rendering (textContent, createElement)         │
└──────────────────────────┬─────────────────────────────┘
                           │ HTTP / JSON (Session Cookie)
                           ▼
┌────────────────────────────────────────────────────────┐
│                   Flask Application                    │
│  - App Factory (backend/create_app)                    │
│  - Blueprints: /api/auth and /api/tasks                │
│  - Flask-Login Session Management                      │
│  - Server-Side Input Validation                        │
└──────────────────────────┬─────────────────────────────┘
                           │ ORM Models & Queries
                           ▼
┌────────────────────────────────────────────────────────┐
│               SQLAlchemy / Flask-SQLAlchemy            │
│  - User Model (Password hashing via Werkzeug)          │
│  - Task Model (Foreign keys, cascade delete, indexes)  │
└──────────────────────────┬─────────────────────────────┘
                           │ SQL Queries
                           ▼
┌────────────────────────────────────────────────────────┐
│                    SQLite Database                     │
│  - instance/task_manager.db (Local development)        │
└────────────────────────────────────────────────────────┘
```

---

## Database Design

### User Model (`users`)

| Field | Type | Attributes | Description |
| :--- | :--- | :--- | :--- |
| `id` | Integer | Primary Key, Auto-increment | Unique identifier |
| `name` | String(80) | Not Null | User full name (2–80 chars) |
| `email` | String(120) | Unique, Indexed, Not Null | Normalized (`strip().lower()`) |
| `password_hash` | String(255) | Not Null | Hashed password (never exposed) |
| `created_at` | DateTime | Default UTC | Account creation timestamp |

### Task Model (`tasks`)

| Field | Type | Attributes | Description |
| :--- | :--- | :--- | :--- |
| `id` | Integer | Primary Key, Auto-increment | Unique identifier |
| `user_id` | Integer | Foreign Key (`users.id`), Indexed | Scoped task owner (`ondelete='CASCADE'`) |
| `title` | String(120) | Not Null | Task title (1–120 chars) |
| `description` | Text | Nullable | Optional notes (up to 1000 chars) |
| `status` | String(20) | Not Null, Default `'pending'` | `'pending'` or `'completed'` |
| `priority` | String(20) | Not Null, Default `'medium'` | `'low'`, `'medium'`, or `'high'` |
| `due_date` | Date | Nullable | Optional deadline date |
| `created_at` | DateTime | Default UTC | Creation timestamp |
| `updated_at` | DateTime | Default UTC, Auto-update | Last modification timestamp |
| `completed_at` | DateTime | Nullable | Timestamp when completed; `null` when reopened |

---

## API Endpoints

### Authentication (`/api/auth`)

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/auth/register` | Register new account and log in | No |
| `POST` | `/api/auth/login` | Authenticate user & start session | No |
| `POST` | `/api/auth/logout` | Terminate session | Yes |
| `GET` | `/api/auth/me` | Retrieve authenticated user profile | Yes |

### Tasks (`/api/tasks`)

| Method | Endpoint | Query Parameters / Payload | Description | Auth Required |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/tasks` | `status`, `priority`, `search`, `sort` | List user's tasks with filter/sort | Yes |
| `POST` | `/api/tasks` | `{ title, description, priority, due_date }` | Create a new task | Yes |
| `GET` | `/api/tasks/<id>` | - | Retrieve single task | Yes |
| `PUT` | `/api/tasks/<id>` | `{ title, description, priority, status, due_date }` | Update task details | Yes |
| `PATCH`| `/api/tasks/<id>/toggle` | - | Toggle completed / reopened status | Yes |
| `DELETE`| `/api/tasks/<id>`| - | Delete task | Yes |
| `GET` | `/api/tasks/stats` | - | Return `{ total, pending, completed, overdue }` | Yes |

### Health Check

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Returns server health status `{"status": "ok"}` |

---

## Project Structure

```
TaskFlow/
│
├── backend/
│   ├── __init__.py          # Flask application factory, blueprints & routes
│   ├── models.py            # User and Task SQLAlchemy database models
│   ├── utils.py             # Server validation, email regex, date helpers
│   │
│   ├── auth/
│   │   ├── __init__.py      # Auth Blueprint initialization (/api/auth)
│   │   └── routes.py        # Registration, login, logout, me routes
│   │
│   └── tasks/
│       ├── __init__.py      # Tasks Blueprint initialization (/api/tasks)
│       └── routes.py        # Task CRUD, toggle, statistics & filter routes
│
├── frontend/
│   ├── index.html           # Main dashboard page
│   ├── login.html           # Authentication sign-in page
│   ├── register.html        # User registration page
│   │
│   ├── css/
│   │   └── styles.css       # Complete design system, dark mode, responsive CSS
│   │
│   └── js/
│       ├── api.js           # API fetch wrapper, toast engine, theme switcher
│       ├── auth.js          # Auth forms controller, live password strength
│       └── app.js           # Dashboard controller, CRUD, search, modals
│
├── tests/
│   ├── conftest.py          # Pytest fixtures and in-memory test database
│   ├── test_auth.py         # Authentication and validation tests
│   └── test_tasks.py        # Task CRUD, stats, and security isolation tests
│
├── instance/                # SQLite instance directory (gitignored)
│   └── task_manager.db
│
├── .env.example             # Template environment configuration
├── .gitignore               # Ignored secrets, database files, and caches
├── requirements.txt         # Pinned Python package dependencies
├── run.py                   # Local development server entrypoint
├── seed.py                  # Demo seed script for testing
└── README.md                # Project documentation
```

---

## Local Setup & Quickstart

### 1. Prerequisites

- Python 3.10+ installed
- Git

### 2. Clone the Repository

```bash
git clone https://github.com/nandh/TaskFlow.git
cd TaskFlow
```

### 3. Create and Activate a Virtual Environment

**On Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**On macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

The default `.env` is configured for local development:
```ini
FLASK_APP=run.py
FLASK_ENV=development
FLASK_DEBUG=1
SECRET_KEY=tf-local-dev-secret-984e1b8c2a4f0d7e5b3c1a9
DATABASE_URL=sqlite:///task_manager.db
SESSION_COOKIE_SECURE=False
```

### 6. (Optional) Seed Demo Data

Run the seeder to populate a demo account with starter tasks:

```bash
python seed.py
```

Demo Credentials:
- **Email**: `demo@taskflow.dev`
- **Password**: `TaskFlow2026!`

### 7. Run the Application

```bash
python run.py
```

The application will be accessible at:
👉 **`http://127.0.0.1:5000`**

- Unauthenticated visits automatically route to `/login.html`.
- Authenticated users directly land on `/` (the dashboard).

---

## Running the Automated Test Suite

Run the full pytest suite with verbose output:

```bash
pytest -v
```

All 17 tests verify:
- Registration success, duplicate rejection, and field validations.
- Password hashing security (passwords are never saved in plaintext).
- Login credentials check and unauthorized route rejections (401 JSON).
- Task creation, updating, completion toggle, and deletion.
- Task search, priority filter, status filter, and multi-field sorting.
- Overdue computation and statistics calculations.
- **Strict User Isolation**: Verified that User A cannot view, update, delete, or calculate stats for User B's tasks under any condition.

---

## Security Considerations

1. **Password Encryption**: All passwords are encrypted with Werkzeug's secure key derivation (`generate_password_hash`).
2. **Session Cookie Security**: Cookies are configured with `HttpOnly=True` (mitigates XSS cookie theft) and `SameSite='Lax'` (mitigates CSRF).
3. **Session-Derived Ownership**: Task endpoints strictly derive ownership from `current_user.id`. The frontend client can never spoof ownership by supplying an arbitrary `user_id`.
4. **Information Disclosure Prevention**: Querying tasks belonging to another user returns HTTP 404 rather than 403, preventing attackers from enumerating valid task IDs.
5. **DOM Sanitization**: User-generated task titles and descriptions are appended exclusively via `textContent` and safe DOM elements, preventing cross-site scripting (XSS).
6. **Security Headers**: Standard security headers (`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection`) are applied to all Flask responses.

---

## Accessibility & UI/UX Highlights

- **Semantic HTML**: Proper `<header>`, `<main>`, `<section>`, `<article>`, and `<button>` elements.
- **Focus Indicators**: Clear focus rings (`:focus-visible`) for all interactive buttons and inputs.
- **Accessible Dialogs**: Modals include `role="dialog"`, `aria-modal="true"`, `aria-labelledby`, and dismiss on `Escape`.
- **Live Statuses**: Checkboxes provide dynamic `aria-label` indicators for screen readers.
- **Micro-Interactions**: Smooth hover elevations, button state changes, and compliance with `prefers-reduced-motion`.

---

## What Was Learned

- Implementing a clean **Application Factory** pattern in Flask that serves static assets alongside REST blueprints.
- Designing an in-memory SQLite testing configuration with SQLAlchemy's `StaticPool` to verify cross-user isolation.
- Structuring vanilla JavaScript applications into modular concerns (API, Auth, App State) without heavy frontend build tools.
- Crafting a CSS variables design system with first-class light and dark modes.

---

## Future Enhancements

- Task categories / tags for multi-project grouping.
- Sub-tasks / checklists within individual task cards.
- Export tasks to CSV or Markdown.
- Drag-and-drop Kanban view option.
- PostgreSQL adapter configuration for enterprise scale.

---

## License

This project is licensed under the MIT License.
