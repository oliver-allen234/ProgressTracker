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

## Next Steps

### 1. Views — Training (admin only for CUD)
- [ ] `TrainingListView` — all users, no ownership filter
- [ ] `TrainingDetailView` — all users
- [ ] `TrainingCreateView` — staff only (`is_staff` check)
- [ ] `TrainingUpdateView` — staff only
- [ ] `TrainingDeleteView` — staff only

### 2. Views — TrainingAssignment (access control core)
- [ ] `AssignmentListView` — staff see all; regular users filtered to `trainee=request.user`
- [ ] `AssignmentCreateView` — staff only
- [ ] `AssignmentUpdateView` — two forms: managers edit all fields, trainees update status only
- [ ] `AssignmentDeleteView` — staff only

### 3. Forms
- [ ] `TrainingForm` — for create/update of Training modules
- [ ] `AdminAssignmentForm` — full fields for managers
- [ ] `TraineeStatusForm` — status field only for regular users

### 4. URLs
- [ ] Wire up all Training and TrainingAssignment views in `tracker/urls.py`

### 5. Templates
- [ ] `training/training_list.html`
- [ ] `training/training_detail.html`
- [ ] `training/training_form.html`
- [ ] `training/training_confirm_delete.html`
- [ ] `assignments/assignment_list.html`
- [ ] `assignments/assignment_form.html`
- [ ] `assignments/assignment_confirm_delete.html`
- [ ] Update `dashboard.html` — manager view shows team completion rates
- [ ] Update `base.html` — add nav links for Training and Assignments

### 6. Manager Dashboard
- [ ] Team completion rate per training module
- [ ] Per-user assignment status overview
- [ ] Replace competitive leaderboard with compliance summary for staff view

### 7. OWASP Security (must demonstrate 3+)
- [ ] **A01 Broken Access Control** — enforce `is_staff` on all Training CUD views; enforce `trainee=request.user` on assignment updates; add tests proving non-owners are blocked
- [ ] **A03 SQL Injection** — document ORM usage, no raw SQL; add to report
- [ ] **A07 CSRF** — verify `{% csrf_token %}` in all forms; demonstrate a POST without token is rejected
- [ ] Capture screenshots/video evidence of each defence

### 8. Testing
- [ ] Model tests — `Training`, `TrainingAssignment` field validation
- [ ] View tests — auth checks (logged-out redirect, non-staff blocked)
- [ ] Access control tests — regular user cannot access another user's assignment
- [ ] Security tests — CSRF, ownership enforcement

### 9. DevOps Artefacts (Task 3)
- [ ] GitHub Actions CI workflow (`.github/workflows/django.yml`) — runs tests on push
- [ ] `Dockerfile` and `docker-compose.yml`
- [ ] `bandit` security scan — capture output as evidence
- [ ] `coverage` report

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
