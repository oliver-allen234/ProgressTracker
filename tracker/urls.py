from django.urls import path
from . import views
urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),

    path('tasks/', views.TaskListView.as_view(), name='task-list'),
    path('tasks/create/', views.TaskCreateView.as_view(), name='task-create'),
    path('tasks/<int:pk>/update/', views.TaskUpdateView.as_view(), name='task-update'),
    path('tasks/<int:pk>/delete/', views.TaskDeleteView.as_view(), name='task-delete'),
    path('tasks/<int:pk>/toggle/', views.toggle_task_completion, name='task-toggle'),
    path('tasks/completion-data/', views.task_completion_data, name='task-completion-data'),

    path('goals/', views.GoalListView.as_view(), name='goal-list'),
    path('goals/create/', views.GoalCreateView.as_view(), name='goal-create'),
    path('goals/<int:pk>/', views.GoalDetailView.as_view(), name='goal-detail'),
    path('goals/<int:pk>/update/', views.GoalUpdateView.as_view(), name='goal-update'),
    path('goals/<int:pk>/delete/', views.GoalDeleteView.as_view(), name='goal-delete'),
    path('goals/<int:goal_id>/add-task/', views.add_task_to_goal, name='add-task-to-goal'),
    path('goals/<int:goal_id>/create-task/', views.create_task_for_goal, name='create-task-for-goal'),
    path('goals/<int:goal_id>/tasks/<int:task_id>/toggle/', views.toggle_goal_task_completion, name='toggle-goal-task'),
    path('goals/<int:goal_id>/log-hours/', views.log_hours, name='log-hours'),

    path('community/', views.community_view, name='community'),
    path('users/<int:user_id>/', views.user_detail_view, name='user-detail'),
    path('users/<int:user_id>/delete/', views.delete_user, name='delete-user'),

    path('trainings/', views.TrainingListView.as_view(), name='training-list'),
    path('trainings/create/', views.TrainingCreateView.as_view(), name='training-create'),
    path('trainings/<int:pk>/', views.TrainingDetailView.as_view(), name='training-detail'),
    path('trainings/<int:pk>/update/', views.TrainingUpdateView.as_view(), name='training-update'),
    path('trainings/<int:pk>/delete/', views.TrainingDeleteView.as_view(), name='training-delete'),

    path('assignments/<int:pk>/delete/', views.AssignmentDeleteView.as_view(), name='assignment-delete'),
    path('assignments/', views.AssignmentListView.as_view(), name='assignment-list'),
    path('assignments/create/', views.AssignmentCreateView.as_view(), name='assignment-create'),
    path('assignments/<int:pk>/update/', views.AssignmentUpdateView.as_view(), name='assignment-update'),

]
