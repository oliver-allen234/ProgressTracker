# Trackwise

A dual-purpose Django web application built for a Level 6 Software Engineering & DevOps assessment (QAC020X328).

**Live demo:** https://oliverallen234.pythonanywhere.com

---

## Overview

Trackwise serves two distinct user roles:

- **Regular users** — track personal goals, tasks, and progress on a community leaderboard
- **Managers (staff)** — create and manage team training modules, assign them to users, and monitor compliance via a dedicated dashboard

---

## Features

### Personal (all users)
- User registration and login
- CRUD for Goals and Tasks with priority, status, and due dates
- Hour logging against goals
- Task completion trend chart (7-day view)
- Community leaderboard

### Team Training (staff only)
- Create, edit, and delete training modules (catalogue)
- Assign modules to team members with due dates and notes
- Trainees can update their own assignment status
- Manager dashboard: per-module completion rates and per-user assignment status

---

## Security (OWASP)

| Threat | Defence |
|---|---|
| A01 Broken Access Control | `AdminRequiredMixin` with `raise_exception=True` enforces `is_staff` on all Training/Assignment CUD views; cross-user assignment updates blocked via `test_func` |
| A03 SQL Injection | All database access uses the Django ORM — no raw SQL |
| A07 CSRF | `{% csrf_token %}` in every POST form; `CsrfViewMiddleware` active; `CSRF_TRUSTED_ORIGINS` set for HTTPS |

---

## Tech Stack

- Python 3.11 / Django 5.2
- SQLite (development) 
- WhiteNoise for static file serving
- Bootstrap 5 + Chart.js

---

## Getting Started

**Deployed app:** https://oliverallen234.pythonanywhere.com

Or run locally:

```bash
git clone https://github.com/oliver-allen234/ProgressTracker.git
cd ProgressTracker

python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

pip install -r requirements.txt

python manage.py migrate
python manage.py runserver
```

---

## User Roles

| Action | Regular User | Manager (is_staff) |
|---|---|---|
| Browse Training catalogue | ✓ | ✓ |
| Create/Edit/Delete Training | ✗ | ✓ |
| View own assignments | ✓ | ✓ |
| View all team assignments | ✗ | ✓ |
| Assign training to a user | ✗ | ✓ |
| Update own assignment status | ✓ | ✓ |
| Delete an assignment | ✗ | ✓ |

---

## Testing

22 tests across three suites:

- `ModelTests` — existing Goal/Task/Profile model validation
- `TrainingModelTests` — Training and TrainingAssignment field validation
- `TrainingViewAuthTests` — login redirect and 403 enforcement for non-staff
- `AssignmentAccessControlTests` — cross-user isolation, role-based queryset filtering

```bash
python manage.py test tracker
```

**Coverage:** 59% overall (100% migrations, admin, tests — 39% views)

```bash
pip install coverage
coverage run manage.py test tracker
coverage report --include="tracker/*"
```

---

## DevOps

| Artefact | Purpose |
|---|---|
| `.github/workflows/django.yml` | CI: runs tests and bandit security scan on every push/PR |
| `Dockerfile` | Containerised build using Python 3.11-slim |
| `docker-compose.yml` | Single-service local container setup |

**Bandit scan:** 0 issues across 1,236 lines of code.

```bash
pip install bandit
bandit -r tracker/ -x tracker/tests.py
```

---

## Design Pattern

Trackwise follows Django's **MVT (Model-View-Template)** pattern:

- **Models** — data structure and relationships (`Goal`, `Task`, `Training`, `TrainingAssignment`, etc.)
- **Views** — business logic, access control, and context preparation
- **Templates** — Bootstrap 5 HTML with role-aware rendering
