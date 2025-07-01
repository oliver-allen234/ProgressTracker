from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django import forms
from django.utils import timezone
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.db.models import Count, Sum, Q
from django.db import transaction

from .models import UserTask, Goal, Task, HourLog, Profile, Progress

# Custom mixins for permission handling
class AdminRequiredMixin(UserPassesTestMixin):
    """
    Mixin that requires the user to be an admin (staff)
    """
    def test_func(self):
        return self.request.user.is_staff

class RegularUserMixin(UserPassesTestMixin):
    """
    Mixin that ensures regular users can only access their own data
    """
    def test_func(self):
        # Get the object being accessed
        obj = self.get_object()

        # Check if the user is the owner of the object or an admin
        if hasattr(obj, 'user'):
            return obj.user == self.request.user or self.request.user.is_staff
        return False


@login_required
def dashboard(request):
    # Get tasks counts
    completed_tasks_count = UserTask.objects.filter(
        user=request.user,
        is_completed=True
    ).count()

    # Get all goals count
    total_goals_count = Goal.objects.filter(
        user=request.user
    ).count()

    # Get completed goals count
    completed_goals_count = Goal.objects.filter(
        user=request.user,
        status='COMPLETED'
    ).count()

    # Get current goals (not completed)
    current_goals = Goal.objects.filter(
        user=request.user
    ).exclude(
        status='COMPLETED'
    ).order_by('priority', 'target_date')

    # Calculate goals completion percentage
    goals_completion_percentage = 0
    if total_goals_count > 0:
        goals_completion_percentage = int((completed_goals_count / total_goals_count) * 100)

    # Get community leaderboard data
    # Get all users including the current user
    users = User.objects.all().order_by('username')

    # Calculate statistics for each user
    user_stats = []
    for user in users:
        # Get completed goals count
        user_completed_goals_count = Goal.objects.filter(
            user=user,
            status='COMPLETED'
        ).count()

        # Get total goals count
        user_total_goals_count = Goal.objects.filter(
            user=user
        ).count()

        # Calculate goals completion percentage
        user_goals_completion_percentage = 0
        if user_total_goals_count > 0:
            user_goals_completion_percentage = int((user_completed_goals_count / user_total_goals_count) * 100)

        # Get completed tasks count
        user_completed_tasks_count = UserTask.objects.filter(
            user=user,
            is_completed=True
        ).count()

        # Add user stats to the list
        user_stats.append({
            'user': user,
            'completed_goals_count': user_completed_goals_count,
            'total_goals_count': user_total_goals_count,
            'goals_completion_percentage': user_goals_completion_percentage,
            'completed_tasks_count': user_completed_tasks_count,
            'is_current_user': user.id == request.user.id,  # Flag to identify the current user
        })

    # Sort users by completed tasks count (descending)
    user_stats.sort(key=lambda x: x['completed_tasks_count'], reverse=True)

    # Limit to top 3 users for the dashboard
    top_users = user_stats[:3] if user_stats else []

    context = {
        'completed_tasks_count': completed_tasks_count,
        'total_goals_count': total_goals_count,
        'completed_goals_count': completed_goals_count,
        'goals_completion_percentage': goals_completion_percentage,
        'current_goals': current_goals,
        'top_users': top_users,
        'is_admin': request.user.is_staff,
    }

    return render(request, 'dashboard.html', context)

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'Login Successful!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'login.html')

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Check if the 'is_admin' parameter is present in the request
            # This is just for testing purposes and would be removed in production
            if request.POST.get('is_admin') == 'true':
                user.is_staff = True
                user.save()
                messages.success(request, 'Admin user created successfully!')
            else:
                messages.success(request, 'Registration successful!')

            login(request, user)
            return redirect('dashboard')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully!')
    return redirect('dashboard')


# Task Form
class UserTaskForm(forms.ModelForm):
    class Meta:
        model = UserTask
        fields = ['title', 'description', 'status', 'priority', 'due_date']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean_due_date(self):
        due_date = self.cleaned_data.get('due_date')
        if due_date and due_date < timezone.now().date():
            raise forms.ValidationError("Due date cannot be in the past.")
        return due_date

# Admin Task Form with user selection
class AdminUserTaskForm(UserTaskForm):
    user = forms.ModelChoiceField(
        queryset=User.objects.all().order_by('username'),
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True
    )

    class Meta(UserTaskForm.Meta):
        fields = ['user'] + UserTaskForm.Meta.fields


# Task Views
class TaskListView(LoginRequiredMixin, ListView):
    model = UserTask
    template_name = 'tasks/task_list.html'
    context_object_name = 'tasks'

    def get_queryset(self):
        # Filter tasks to show only those belonging to the current user
        return UserTask.objects.filter(user=self.request.user).order_by('due_date', 'priority')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['today'] = timezone.now().date()
        return context


class TaskCreateView(LoginRequiredMixin, CreateView):
    model = UserTask
    template_name = 'tasks/task_form.html'
    success_url = reverse_lazy('task-list')

    def get_form_class(self):
        # Use AdminUserTaskForm for admin users, UserTaskForm for regular users
        if self.request.user.is_staff:
            return AdminUserTaskForm
        return UserTaskForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_admin'] = self.request.user.is_staff
        return context

    def form_valid(self, form):
        # For admin users, the user is selected in the form
        # For regular users, set the user to the current logged-in user
        if not self.request.user.is_staff or not form.cleaned_data.get('user'):
            form.instance.user = self.request.user
        messages.success(self.request, 'Task created successfully!')
        return super().form_valid(form)


class TaskUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = UserTask
    template_name = 'tasks/task_form.html'
    success_url = reverse_lazy('task-list')

    def get_form_class(self):
        # Use AdminUserTaskForm for admin users, UserTaskForm for regular users
        if self.request.user.is_staff:
            return AdminUserTaskForm
        return UserTaskForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_admin'] = self.request.user.is_staff
        return context

    def test_func(self):
        # Get the task
        task = self.get_object()

        # Admins can update any task
        if self.request.user.is_staff:
            return True

        # Regular users can only update their own tasks
        return task.user == self.request.user

    def get_queryset(self):
        # Admins can see all tasks, regular users only their own
        if self.request.user.is_staff:
            return UserTask.objects.all()
        return UserTask.objects.filter(user=self.request.user)

    def form_valid(self, form):
        # For admin users, the user can be changed in the form
        # For regular users, ensure the user remains the same
        if not self.request.user.is_staff:
            form.instance.user = self.request.user
        messages.success(self.request, 'Task updated successfully!')
        return super().form_valid(form)


class TaskDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = UserTask
    template_name = 'tasks/task_confirm_delete.html'
    success_url = reverse_lazy('task-list')

    def test_func(self):
        # Only admins can delete tasks
        if self.request.user.is_staff:
            return True
        # Regular users can't delete tasks
        return False

    def get_queryset(self):
        # Admins can delete any task, regular users none
        if self.request.user.is_staff:
            return UserTask.objects.all()
        return UserTask.objects.none()

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Task deleted successfully!')
        return super().delete(request, *args, **kwargs)


@login_required
def toggle_task_completion(request, pk):
    task = get_object_or_404(UserTask, pk=pk, user=request.user)
    task.is_completed = not task.is_completed

    # Update status if task is completed
    if task.is_completed and task.status != 'COMPLETED':
        task.status = 'COMPLETED'
    elif not task.is_completed and task.status == 'COMPLETED':
        task.status = 'TODO'

    task.save()
    messages.success(request, f'Task "{task.title}" marked as {"completed" if task.is_completed else "incomplete"}.')
    return redirect('task-list')




# Goal Form
class GoalForm(forms.ModelForm):
    class Meta:
        model = Goal
        fields = ['title', 'description', 'status', 'priority', 'categories', 'target_date']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'categories': forms.SelectMultiple(attrs={'class': 'form-select'}),
            'target_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean_target_date(self):
        target_date = self.cleaned_data.get('target_date')
        if target_date and target_date < timezone.now().date():
            raise forms.ValidationError("Target date cannot be in the past.")
        return target_date


# Goal Views
class GoalListView(LoginRequiredMixin, ListView):
    model = Goal
    template_name = 'goals/goal_list.html'
    context_object_name = 'goals'

    def get_queryset(self):
        # Filter goals to show only those belonging to the current user
        return Goal.objects.filter(user=self.request.user).order_by('priority')


class GoalDetailView(LoginRequiredMixin, DetailView):
    model = Goal
    template_name = 'goals/goal_detail.html'
    context_object_name = 'goal'

    def get_queryset(self):
        # Ensure users can only view their own goals
        return Goal.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add user tasks that are not linked to any goal
        context['user_tasks'] = UserTask.objects.filter(
            user=self.request.user,
            is_completed=False
        )
        # Add today's date for highlighting overdue tasks
        context['today'] = timezone.now().date()
        # Add hour logs for this goal, ordered by date (newest first)
        context['hour_logs'] = self.object.hour_logs.all().order_by('-date')
        return context


class GoalCreateView(LoginRequiredMixin, CreateView):
    model = Goal
    form_class = GoalForm
    template_name = 'goals/goal_form.html'
    success_url = reverse_lazy('goal-list')

    def form_valid(self, form):
        # Set the user to the current logged-in user
        form.instance.user = self.request.user
        messages.success(self.request, 'Goal created successfully!')
        return super().form_valid(form)


class GoalUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Goal
    form_class = GoalForm
    template_name = 'goals/goal_form.html'
    success_url = reverse_lazy('goal-list')

    def test_func(self):
        # Get the goal
        goal = self.get_object()

        # Admins can update any goal
        if self.request.user.is_staff:
            return True

        # Regular users can only update their own goals
        return goal.user == self.request.user

    def get_queryset(self):
        # Admins can see all goals, regular users only their own
        if self.request.user.is_staff:
            return Goal.objects.all()
        return Goal.objects.filter(user=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Goal updated successfully!')
        return super().form_valid(form)


class GoalDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Goal
    template_name = 'goals/goal_confirm_delete.html'
    success_url = reverse_lazy('goal-list')

    def test_func(self):
        # Only admins can delete goals
        if self.request.user.is_staff:
            return True
        # Regular users can't delete goals
        return False

    def get_queryset(self):
        # Admins can delete any goal, regular users none
        if self.request.user.is_staff:
            return Goal.objects.all()
        return Goal.objects.none()

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Goal deleted successfully!')
        return super().delete(request, *args, **kwargs)


@login_required
def add_task_to_goal(request, goal_id):
    goal = get_object_or_404(Goal, id=goal_id, user=request.user)

    if request.method == 'POST':
        task_id = request.POST.get('task_id')
        if task_id:
            task = get_object_or_404(UserTask, id=task_id, user=request.user)

            # Create a Task object linked to the Goal
            Task.objects.create(
                goal=goal,
                title=task.title,
                description=task.description,
                is_completed=task.is_completed,
                due_date=task.due_date
            )

            messages.success(request, f'Task "{task.title}" added to goal "{goal.title}".')

    return redirect('goal-detail', pk=goal.id)


# Task Form for Goal-specific tasks
class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'is_completed', 'due_date']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean_due_date(self):
        due_date = self.cleaned_data.get('due_date')
        if due_date and due_date < timezone.now().date():
            raise forms.ValidationError("Due date cannot be in the past.")
        return due_date

# Hour Log Form
class HourLogForm(forms.ModelForm):
    class Meta:
        model = HourLog
        fields = ['hours', 'date', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean_hours(self):
        hours = self.cleaned_data.get('hours')
        if hours <= 0:
            raise forms.ValidationError("Hours must be greater than zero.")
        return hours

    def clean_date(self):
        date = self.cleaned_data.get('date')
        if date and date > timezone.now().date():
            raise forms.ValidationError("Date cannot be in the future.")
        return date


@login_required
def create_task_for_goal(request, goal_id):
    goal = get_object_or_404(Goal, id=goal_id, user=request.user)

    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.goal = goal
            task.save()
            messages.success(request, f'Task "{task.title}" created for goal "{goal.title}".')
            return redirect('goal-detail', pk=goal.id)
    else:
        form = TaskForm()

    context = {
        'form': form,
        'goal': goal,
    }
    return render(request, 'goals/task_form.html', context)

@login_required
def toggle_goal_task_completion(request, goal_id, task_id):
    goal = get_object_or_404(Goal, id=goal_id, user=request.user)
    task = get_object_or_404(Task, id=task_id, goal=goal)

    # Toggle completion status
    task.is_completed = not task.is_completed
    task.save()

    # Get updated task count information
    total_tasks = goal.tasks.count()
    completed_tasks = goal.tasks.filter(is_completed=True).count()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # If AJAX request, return JSON response
        return JsonResponse({
            'task_id': task.id,
            'is_completed': task.is_completed,
            'completion_percentage': goal.get_completion_percentage(),
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks
        })
    else:
        # If regular request, redirect back to goal detail page
        messages.success(request, f'Task "{task.title}" marked as {"completed" if task.is_completed else "incomplete"}.')
        return redirect('goal-detail', pk=goal.id)

@login_required
def log_hours(request, goal_id):
    goal = get_object_or_404(Goal, id=goal_id, user=request.user)

    if request.method == 'POST':
        form = HourLogForm(request.POST)
        if form.is_valid():
            hour_log = form.save(commit=False)
            hour_log.goal = goal
            hour_log.save()
            messages.success(request, f'Successfully logged {hour_log.hours} hours for "{goal.title}".')
            return redirect('goal-detail', pk=goal.id)
    else:
        form = HourLogForm(initial={'date': timezone.now().date()})

    context = {
        'form': form,
        'goal': goal,
    }
    return render(request, 'goals/hour_log_form.html', context)

@login_required
def community_view(request):
    """
    View for the community page showing all users and their progress.
    Regular users can see a leaderboard of users and their progress.
    Admin users can also remove users.
    """
    # Get all users including the current user
    users = User.objects.all().order_by('username')
    sort_by = request.GET.get('sort_by', 'completed_tasks_count')  # Default sort

    # Calculate statistics for each user
    user_stats = []
    for user in users:
        # Get completed goals count
        completed_goals_count = Goal.objects.filter(
            user=user,
            status='COMPLETED'
        ).count()

        # Get total goals count
        total_goals_count = Goal.objects.filter(
            user=user
        ).count()

        # Calculate goals completion percentage
        goals_completion_percentage = 0
        if total_goals_count > 0:
            goals_completion_percentage = int((completed_goals_count / total_goals_count) * 100)

        # Get completed tasks count
        completed_tasks_count = UserTask.objects.filter(
            user=user,
            is_completed=True
        ).count()

        # Get completed tasks count
        tasks_in_progress_count = UserTask.objects.filter(
            user=user,
            is_completed=False
        ).count()

        # Get total hours logged
        total_hours = HourLog.objects.filter(
            goal__user=user
        ).aggregate(Sum('hours'))['hours__sum'] or 0

        # Add user stats to the list
        user_stats.append({
            'user': user,
            'completed_goals_count': completed_goals_count,
            'total_goals_count': total_goals_count,
            'goals_completion_percentage': goals_completion_percentage,
            'completed_tasks_count': completed_tasks_count,
            'tasks_in_progress_count': tasks_in_progress_count,
            'total_hours': total_hours,
            'is_current_user': user.id == request.user.id,  # Flag to identify the current user
        })

    # Sort users by completed tasks count (descending)
    if sort_by in ['completed_goals_count', 'total_goals_count', 'goals_completion_percentage', 'completed_tasks_count',
                   'total_hours']:
        user_stats.sort(key=lambda x: x[sort_by], reverse=True)
    else:
        user_stats.sort(key=lambda x: x['completed_tasks_count'], reverse=True)  # Fallback

    context = {
        'user_stats': user_stats,
        'is_admin': request.user.is_staff,
        'sort_by': sort_by,
    }

    return render(request, 'community.html', context)

@login_required
def user_detail_view(request, user_id):
    """
    View for displaying details about a specific user.
    """
    user = get_object_or_404(User, id=user_id)

    # Get completed goals count
    completed_goals_count = Goal.objects.filter(
        user=user,
        status='COMPLETED'
    ).count()

    # Get total goals count
    total_goals_count = Goal.objects.filter(
        user=user
    ).count()

    # Calculate goals completion percentage
    goals_completion_percentage = 0
    if total_goals_count > 0:
        goals_completion_percentage = int((completed_goals_count / total_goals_count) * 100)

    # Get completed tasks count
    completed_tasks_count = UserTask.objects.filter(
        user=user,
        is_completed=True
    ).count()

    # Get total hours logged
    total_hours = HourLog.objects.filter(
        goal__user=user
    ).aggregate(Sum('hours'))['hours__sum'] or 0

    # Get current goals (not completed)
    current_goals = Goal.objects.filter(
        user=user
    ).exclude(
        status='COMPLETED'
    ).order_by('priority', 'target_date')

    # Get community leaderboard data
    # Get all users except the profile user (we still want to exclude the profile user since they have their own stats displayed separately)
    users = User.objects.exclude(id=user_id).order_by('username')

    # Calculate statistics for each user
    user_stats = []
    for u in users:
        # Get completed goals count
        user_completed_goals_count = Goal.objects.filter(
            user=u,
            status='COMPLETED'
        ).count()

        # Get total goals count
        user_total_goals_count = Goal.objects.filter(
            user=u
        ).count()

        # Calculate goals completion percentage
        user_goals_completion_percentage = 0
        if user_total_goals_count > 0:
            user_goals_completion_percentage = int((user_completed_goals_count / user_total_goals_count) * 100)

        # Get completed tasks count
        user_completed_tasks_count = UserTask.objects.filter(
            user=u,
            is_completed=True
        ).count()

        # Add user stats to the list
        user_stats.append({
            'user': u,
            'completed_goals_count': user_completed_goals_count,
            'total_goals_count': user_total_goals_count,
            'goals_completion_percentage': user_goals_completion_percentage,
            'completed_tasks_count': user_completed_tasks_count,
            'is_current_user': u.id == request.user.id,  # Flag to identify the current user
        })

    # Sort users by goals completion percentage (descending)
    user_stats.sort(key=lambda x: x['goals_completion_percentage'], reverse=True)

    # Limit to top 3 users for the dashboard
    top_users = user_stats[:3] if user_stats else []

    context = {
        'profile_user': user,
        'completed_goals_count': completed_goals_count,
        'total_goals_count': total_goals_count,
        'goals_completion_percentage': goals_completion_percentage,
        'completed_tasks_count': completed_tasks_count,
        'total_hours': total_hours,
        'current_goals': current_goals,
        'top_users': top_users,
        'is_admin': request.user.is_staff,
    }

    return render(request, 'user_detail.html', context)

@login_required
@transaction.atomic
def delete_user(request, user_id):
    """
    View for admins to delete users.
    """
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to delete users.")
        return redirect('community')

    user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        username = user.username

        # Check if the user is trying to delete their own account
        is_self = user.id == request.user.id

        try:
            # Manually delete related objects to ensure proper order
            # First, delete all goals and their related objects
            goals = Goal.objects.filter(user=user)
            for goal in goals:
                # Clear the many-to-many relationship with categories
                goal.categories.clear()
                # Delete tasks related to this goal
                Task.objects.filter(goal=goal).delete()
                # Delete progress updates related to this goal
                Progress.objects.filter(goal=goal).delete()
                # Delete hour logs related to this goal
                HourLog.objects.filter(goal=goal).delete()
                # Now delete the goal
                goal.delete()

            # Delete user tasks
            UserTask.objects.filter(user=user).delete()

            # Delete profile
            try:
                if hasattr(user, 'profile'):
                    user.profile.delete()
            except Profile.DoesNotExist:
                pass

            # Finally delete the user
            user.delete()

            # If the user deleted their own account, log them out and redirect to home
            if is_self:
                logout(request)
                messages.success(request, f'Your account has been deleted.')
                return redirect('dashboard')

            # Otherwise, show success message and redirect to community page
            messages.success(request, f'User "{username}" has been deleted.')
            return redirect('community')

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Error deleting user: {str(e)}\n{error_details}")
            messages.error(request, f"Error deleting user: {str(e)}")
            return redirect('user-detail', user_id=user_id)

    context = {
        'user_to_delete': user,
        'is_self': user.id == request.user.id,
    }

    return render(request, 'delete_user.html', context)
