# Trackwise - The Personal Progress Tracker
A Django application that allows users to track personal goals and tasks, monitor performance, and compare progress with others on a community leaderboard.

Designed for individuals or small teams to take control of their development!

## Features

- User registration and login
- CRUD operations for Goal and Task tracking
- Dashboard with performance visualisation and competitive leaderboard
- Role-based access, Admin controls for teams

## Design Patterns

**MVC Pattern**
Trackwise follows the Model-View-Controller design pattern implementation through Django's framework. This separates business logic from presentation logic, making the development and testing process more efficient.

**Models** handles the data structure and relationships (e.g., Goal, Task, UserTask). Indicated here: ErDiagram.mermaid

**Views** manages the core logic and user variables (e.g., goal creation, leaderboard filtering).

**Templates** act as the frontend (HTML), creating a visual structure 



## Getting Started

Check out the deployed application - https://oliverallen234.pythonanywhere.com/

OR

1. Clone the repository:

```
bash

git clone https://github.com/oliver-allen234/ProgressTracker.git
cd ProgressTracker
```

2. Create and activate a virtual environment

```
bash

python -m venv venv
venv\Scripts\activate
```

3. Install Dependencies

```
bash

pip install -r requirements.txt
```

3. Run the app

```
bash

python manage.py runserver
```

#### 5. **Requirements**
```markdown
## Requirements

asgiref==3.8.1
colorama==0.4.6
Django==5.2.1
sqlparse==0.5.3
tzdata==2025.2
```


## User Roles

- **Admin**: Full access to all user data, edit/delete rights
- **Regular User**: Can only see and manage their own data
