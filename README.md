# TaskFlow

> **Organize your work. Clear your mind.**

A full-stack personal task manager built with Flask (Python) and Vanilla JavaScript, featuring session-based authentication, real-time productivity statistics, live search, filters, and dark mode.

---

## Project Notes

- **Live Demo**: [https://taskflow-5jo6.onrender.com](https://taskflow-5jo6.onrender.com)
- **Tech Stack**: Python 3, Flask, Flask-SQLAlchemy (SQLite), Flask-Login, Vanilla JavaScript, CSS3 Variables.
- **Strict User Isolation**: Every task query and statistic is scoped to the authenticated session user (`current_user.id`). Other users' tasks return 404 to prevent resource discovery.
- **Task Management**: Create, edit, delete, and toggle tasks between pending and completed with automated completion timestamps.
- **Priority & Due Dates**: Support for Low, Medium, and High priorities, plus due dates with color-coded overdue warnings.
- **Search & Filters**: Instant debounced search, status filter, priority filter, and sort by date, priority, or creation time.
- **UI & Accessibility**: Modern responsive layout, accessible modal dialogs with live character counters, toast notifications, and smooth light/dark theme switcher.
- **Security**: Werkzeug password hashing (passwords never stored in plain text), `HttpOnly` and `SameSite` session cookies, and safe DOM manipulation to eliminate XSS risks.
- **Tests**: 17 automated pytest cases covering auth, task CRUD, and security boundaries (`pytest`).
