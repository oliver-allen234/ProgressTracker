from django.urls import path
from . import views
urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),

    # Task management URLs
    path('tasks/', views.TaskListView.as_view(), name='task-list'),
    path('tasks/create/', views.TaskCreateView.as_view(), name='task-create'),
    path('tasks/<int:pk>/update/', views.TaskUpdateView.as_view(), name='task-update'),
    path('tasks/<int:pk>/delete/', views.TaskDeleteView.as_view(), name='task-delete'),
    path('tasks/<int:pk>/toggle/', views.toggle_task_completion, name='task-toggle'),

    # Goal management URLs
    path('goals/', views.GoalListView.as_view(), name='goal-list'),
    path('goals/create/', views.GoalCreateView.as_view(), name='goal-create'),
    path('goals/<int:pk>/', views.GoalDetailView.as_view(), name='goal-detail'),
    path('goals/<int:pk>/update/', views.GoalUpdateView.as_view(), name='goal-update'),
    path('goals/<int:pk>/delete/', views.GoalDeleteView.as_view(), name='goal-delete'),
    path('goals/<int:goal_id>/add-task/', views.add_task_to_goal, name='add-task-to-goal'),
    path('goals/<int:goal_id>/create-task/', views.create_task_for_goal, name='create-task-for-goal'),
    path('goals/<int:goal_id>/tasks/<int:task_id>/toggle/', views.toggle_goal_task_completion, name='toggle-goal-task'),
    path('goals/<int:goal_id>/log-hours/', views.log_hours, name='log-hours'),

    # Community URLs
    path('community/', views.community_view, name='community'),
    path('users/<int:user_id>/', views.user_detail_view, name='user-detail'),
    path('users/<int:user_id>/delete/', views.delete_user, name='delete-user'),
]
