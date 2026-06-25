# Trackwise — Development Plan

## Project Overview
Adapting ProgressTracker into **Trackwise**: a dual-purpose web app that functions as a personal progress tracker for regular users and a team training assignment/monitoring system for managers. Built in Django for a Level 6 Software Engineering & DevOps university assessment (QAC020X328).

---

## Completed

### Repository Housekeeping
- Removed `venv/` and `.idea/` from git tracking (`git rm --cached`)
- Updated `.gitignore` to exclude `venv/`, `.idea/`, `db.sqlite3`, `*.env`

### Schema — Models
- Kept existing: `Profile`, `Goal`, `Task`, `UserTask`, `Progress`, `HourLog`
- Added `Training` — catalogue of training modules, created by managers (staff)
  - Fields: `title`, `description`, `category`, `estimated_hours` (DecimalField), `created_by` (FK→User), `created_at`, `is_active`
- Added `TrainingAssignment` — through model linking User ↔ Training
  - Fields: `training` (FK), `trainee` (FK→User), `assigned_by` (FK→User), `status` (choices: ASSIGNED/IN_PROGRESS/COMPLETED), `assigned_date`, `due_date`, `completed_date`, `notes`
  - Migration: `0003_training_trainingassignment.py`

---

## Completed Tasks

#### June 25, 2026
- Implemented `TrainingListView` to display all active training modules for all users.
- Implemented `TrainingDetailView` to show training details and restrict assignments based on user roles.
- Added `TrainingForm` for creating and updating `Training` modules.
- Implemented `TrainingCreateView` and `TrainingUpdateView` for staff to manage training modules.
- Implemented `AssignmentListView` to display assignments based on user roles.
- Added `AssignmentCreateView` for staff to create training assignments.
- Implemented `AssignmentUpdateView` with role-specific forms for staff and trainees.
- Implemented `AssignmentDeleteView` for staff to remove assignments.
- Wired all Training and Assignment views in `tracker/urls.py`.
- Created all Training templates: `training_list.html`, `training_detail.html`, `training_form.html`, `training_confirm_delete.html`.
- Created all Assignment templates: `assignment_list.html`, `assignment_form.html`, `assignment_confirm_delete.html`.
- Updated `base.html` nav to include Training Modules and Assignments links.
- Fixed `TrainingCreateView`/`TrainingUpdateView` template paths and added `success_url`s.
- Added `success_url` and messages to `AssignmentCreateView`/`AssignmentUpdateView`.

---

## Next Steps

### 1. Views — Training (admin only for CUD)
- [x] `TrainingListView` — all users, no ownership filter
- [x] `TrainingDetailView` — all users
- [x] `TrainingCreateView` — staff only (`is_staff` check)
- [x] `TrainingUpdateView` — staff only
- [x] `TrainingDeleteView` — staff only

### 2. Views — TrainingAssignment (access control core)
- [x] `AssignmentListView` — staff see all; regular users filtered to `trainee=request.user`
- [x] `AssignmentCreateView` — staff only
- [x] `AssignmentUpdateView` — two forms: managers edit all fields, trainees update status only
- [x] `AssignmentDeleteView` — staff only

### 3. Forms
- [x] `TrainingForm` — for create/update of Training modules
- [x] `AdminAssignmentForm` — full fields for managers
- [x] `TraineeStatusForm` — status field only for regular users

### 4. URLs
- [x] Wire up all Training and TrainingAssignment views in `tracker/urls.py`

### 5. Templates
- [x] `trainings/training_list.html`
- [x] `trainings/training_detail.html`
- [x] `trainings/training_form.html`
- [x] `trainings/training_confirm_delete.html`
- [x] `assignments/assignment_list.html`
- [x] `assignments/assignment_form.html`
- [x] `assignments/assignment_confirm_delete.html`
- [x] Update `dashboard.html` — manager view shows team completion rates
- [x] Update `base.html` — add nav links for Training and Assignments

### 6. Manager Dashboard
- [x] Team completion rate per training module
- [x] Per-user assignment status overview (total, in-progress, completed, rate)
- [ ] Replace competitive leaderboard with compliance summary for staff view

### 7. OWASP Security (must demonstrate 3+)
- [x] **A01 Broken Access Control** — `AdminRequiredMixin` with `raise_exception=True` enforces `is_staff` on all Training CUD and Assignment CUD views; `AssignmentUpdateView.test_func` blocks cross-user updates; tests prove non-owners receive 403
- [ ] **A03 SQL Injection** — document ORM usage, no raw SQL; add to report
- [ ] **A07 CSRF** — verify `{% csrf_token %}` in all forms; demonstrate a POST without token is rejected
- [x] Added `403.html` template for clean forbidden responses in production
- [ ] Capture screenshots/video evidence of each defence

### 8. Testing
- [x] Model tests — `Training`, `TrainingAssignment` field validation
- [x] View tests — auth checks (logged-out redirect, non-staff blocked with 403)
- [x] Access control tests — regular user cannot access another user's assignment
- [ ] Security tests — CSRF token enforcement (add to report evidence)

### 9. DevOps Artefacts (Task 3)
- [x] GitHub Actions CI workflow (`.github/workflows/django.yml`) — runs tests and bandit on push/PR
- [x] `Dockerfile` and `docker-compose.yml`
- [x] `bandit` security scan — ran locally, 0 issues across 1236 lines
- [x] `coverage` report — 22 tests, 59% overall (100% migrations/admin/tests, 39% views)

### 10. Deployment
- [ ] Confirm PythonAnywhere deployment is live with new models
- [ ] Verify live link works for submission

### 11. Report (Portfolio document)
- [ ] Task 1 — DevOps overview using CALMS or Three Ways framework
- [ ] Task 2 — App summary, SDLC stages, OWASP evidence
- [ ] Task 3 — DevOps pipeline artefacts with screenshots
- [ ] Cover sheet, table of contents, Harvard references

---

## Access Control Reference

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

## Key Design Decisions
- `is_staff=True` used as the manager flag (consistent with existing codebase)
- No `unique_together` on `TrainingAssignment` — a user can be assigned the same module by multiple managers
- All users can browse the Training catalogue; access control only on CUD operations
- `TrainingAssignment` update uses two forms (pattern matches existing `AdminUserTaskForm` / `UserTaskForm`)
