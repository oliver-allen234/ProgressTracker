# Trackwise - The Personal Progress Tracker
A Django application that allows users to track personal goals and tasks, monitor performance, and compare progress with others on a community leaderboard.

Designed for individuals or small teams to take control of their development!

## Features

- User registration and login
- CRUD operations for Goal and Task tracking
- Dashboard with performance visualisation and competitive leaderboard
- Role-based access, Admin controls for teams

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

```txt
asgiref==3.8.1
colorama==0.4.6
Django==5.2.1
sqlparse==0.5.3
tzdata==2025.2
```


## User Roles

- **Admin**: Full access to all user data, edit/delete rights
- **Regular User**: Can only see and manage their own data
