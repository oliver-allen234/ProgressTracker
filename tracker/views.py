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
from datetime import timedelta
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.db.models import Count, Sum, Q
from django.db import transaction

from .models import UserTask, Goal, Task, HourLog, Profile, Progress


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
        obj = self.get_object()

        if hasattr(obj, 'user'):
            return obj.user == self.request.user or self.request.user.is_staff
        return False


@login_required
def dashboard(request):
    completed_tasks_count = UserTask.objects.filter(
        user=request.user,
        is_completed=True
    ).count()

    total_goals_count = Goal.objects.filter(
        user=request.user
    ).count()

    completed_goals_count = Goal.objects.filter(
        user=request.user,
        status='COMPLETED'
    ).count()

    current_goals = Goal.objects.filter(
        user=request.user
    ).exclude(
        status='COMPLETED'
    ).order_by('priority', 'target_date')

    goals_completion_percentage = 0
    if total_goals_count > 0:
        goals_completion_percentage = int((completed_goals_count / total_goals_count) * 100)

    users = User.objects.all().order_by('username')

    user_stats = []
    for user in users:
        user_completed_goals_count = Goal.objects.filter(
            user=user,
            status='COMPLETED'
        ).count()

        user_total_goals_count = Goal.objects.filter(
            user=user
        ).count()

        user_goals_completion_percentage = 0
        if user_total_goals_count > 0:
            user_goals_completion_percentage = int((user_completed_goals_count / user_total_goals_count) * 100)

        user_completed_tasks_count = UserTask.objects.filter(
            user=user,
            is_completed=True
        ).count()

        user_stats.append({
            'user': user,
            'completed_goals_count': user_completed_goals_count,
            'total_goals_count': user_total_goals_count,
            'goals_completion_percentage': user_goals_completion_percentage,
            'completed_tasks_count': user_completed_tasks_count,
            'is_current_user': user.id == request.user.id,
        })

    user_stats.sort(key=lambda x: x['completed_tasks_count'], reverse=True)

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


class AdminUserTaskForm(UserTaskForm):
    user = forms.ModelChoiceField(
        queryset=User.objects.all().order_by('username'),
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True
    )

    class Meta(UserTaskForm.Meta):
        fields = ['user'] + UserTaskForm.Meta.fields


class TaskListView(LoginRequiredMixin, ListView):
    model = UserTask
    template_name = 'tasks/task_list.html'
    context_object_name = 'tasks'

    def get_queryset(self):
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
        if self.request.user.is_staff:
            return AdminUserTaskForm
        return UserTaskForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_admin'] = self.request.user.is_staff
        return context

    def form_valid(self, form):
        if not self.request.user.is_staff or not form.cleaned_data.get('user'):
            form.instance.user = self.request.user
            if form.instance.is_completed:
                form.instance.completed_date = timezone.now().date()
        messages.success(self.request, 'Task created successfully!')
        return super().form_valid(form)


class TaskUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = UserTask
    template_name = 'tasks/task_form.html'
    success_url = reverse_lazy('task-list')

    def get_form_class(self):
        if self.request.user.is_staff:
            return AdminUserTaskForm
        return UserTaskForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_admin'] = self.request.user.is_staff
        return context

    def test_func(self):
        task = self.get_object()

        if self.request.user.is_staff:
            return True

        return task.user == self.request.user

    def get_queryset(self):
        if self.request.user.is_staff:
            return UserTask.objects.all()
        return UserTask.objects.filter(user=self.request.user)

    def form_valid(self, form):
        if not self.request.user.is_staff:
            form.instance.user = self.request.user
            if form.instance.is_completed and not form.instance.completed_date:
                form.instance.completed_date = timezone.now().date()
            elif not form.instance.is_completed:
                form.instance.completed_date = None
        messages.success(self.request, 'Task updated successfully!')
        return super().form_valid(form)


class TaskDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = UserTask
    template_name = 'tasks/task_confirm_delete.html'
    success_url = reverse_lazy('task-list')

    def test_func(self):
        if self.request.user.is_staff:
            return True
        return False

    def get_queryset(self):
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

    if task.is_completed and task.status != 'COMPLETED':
        task.status = 'COMPLETED'
        task.completed_date = timezone.now().date()
    elif not task.is_completed and task.status == 'COMPLETED':
        task.status = 'TODO'
        task.completed_date = None

    task.save()
    messages.success(request, f'Task "{task.title}" marked as {"completed" if task.is_completed else "incomplete"}.')
    return redirect('task-list')


class GoalForm(forms.ModelForm):
    class Meta:
        model = Goal
        fields = ['title', 'description', 'status', 'priority', 'target_date']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'target_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean_target_date(self):
        target_date = self.cleaned_data.get('target_date')
        if target_date and target_date < timezone.now().date():
            raise forms.ValidationError("Target date cannot be in the past.")
        return target_date


class GoalListView(LoginRequiredMixin, ListView):
    model = Goal
    template_name = 'goals/goal_list.html'
    context_object_name = 'goals'

    def get_queryset(self):
        return Goal.objects.filter(user=self.request.user).order_by('priority')


class GoalDetailView(LoginRequiredMixin, DetailView):
    model = Goal
    template_name = 'goals/goal_detail.html'
    context_object_name = 'goal'

    def get_queryset(self):
        return Goal.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_tasks'] = UserTask.objects.filter(
            user=self.request.user,
            is_completed=False
        )
        context['today'] = timezone.now().date()
        context['hour_logs'] = self.object.hour_logs.all().order_by('-date')
        return context


class GoalCreateView(LoginRequiredMixin, CreateView):
    model = Goal
    form_class = GoalForm
    template_name = 'goals/goal_form.html'
    success_url = reverse_lazy('goal-list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Goal created successfully!')
        return super().form_valid(form)


class GoalUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Goal
    form_class = GoalForm
    template_name = 'goals/goal_form.html'
    success_url = reverse_lazy('goal-list')

    def test_func(self):
        goal = self.get_object()

        if self.request.user.is_staff:
            return True

        return goal.user == self.request.user

    def get_queryset(self):
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
        if self.request.user.is_staff:
            return True
        return False

    def get_queryset(self):
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

            Task.objects.create(
                goal=goal,
                title=task.title,
                description=task.description,
                is_completed=task.is_completed,
                due_date=task.due_date
            )

            messages.success(request, f'Task "{task.title}" added to goal "{goal.title}".')

    return redirect('goal-detail', pk=goal.id)


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
            if task.is_completed:
                task.completed_date = timezone.now().date()
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

    task.is_completed = not task.is_completed
    if task.is_completed:
        task.completed_date = timezone.now().date()
    else:
        task.completed_date = None
    task.save()

    total_tasks = goal.tasks.count()
    completed_tasks = goal.tasks.filter(is_completed=True).count()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'task_id': task.id,
            'is_completed': task.is_completed,
            'completion_percentage': goal.get_completion_percentage(),
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks
        })
    else:
        messages.success(request,
                         f'Task "{task.title}" marked as {"completed" if task.is_completed else "incomplete"}.')
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
    users = User.objects.all().order_by('username')
    sort_by = request.GET.get('sort_by', 'completed_tasks_count')
    valid_sorts = ['completed_goals_count', 'total_goals_count', 'total_hours', 'completed_tasks_count']

    if sort_by not in valid_sorts:
        sort_by = 'completed_tasks_count'

    user_stats = []
    for user in users:
        completed_goals_count = Goal.objects.filter(
            user=user,
            status='COMPLETED'
        ).count()

        total_goals_count = Goal.objects.filter(
            user=user
        ).count()

        goals_completion_percentage = 0
        if total_goals_count > 0:
            goals_completion_percentage = int((completed_goals_count / total_goals_count) * 100)

        completed_tasks_count = UserTask.objects.filter(
            user=user,
            is_completed=True
        ).count()

        tasks_in_progress_count = UserTask.objects.filter(
            user=user,
            is_completed=False
        ).count()

        total_hours = HourLog.objects.filter(
            goal__user=user
        ).aggregate(Sum('hours'))['hours__sum'] or 0

        user_stats.append({
            'user': user,
            'completed_goals_count': completed_goals_count,
            'total_goals_count': total_goals_count,
            'goals_completion_percentage': goals_completion_percentage,
            'completed_tasks_count': completed_tasks_count,
            'tasks_in_progress_count': tasks_in_progress_count,
            'total_hours': total_hours,
            'is_current_user': user.id == request.user.id,
        })

    if sort_by in ['completed_goals_count', 'total_goals_count', 'goals_completion_percentage', 'completed_tasks_count',
                   'total_hours', 'tasks_in_progress_count']:
        user_stats.sort(key=lambda x: x[sort_by], reverse=True)
    else:
        user_stats.sort(key=lambda x: x['completed_tasks_count'], reverse=True)

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

    completed_goals_count = Goal.objects.filter(
        user=user,
        status='COMPLETED'
    ).count()

    total_goals_count = Goal.objects.filter(
        user=user
    ).count()

    goals_completion_percentage = 0
    if total_goals_count > 0:
        goals_completion_percentage = int((completed_goals_count / total_goals_count) * 100)

    completed_tasks_count = UserTask.objects.filter(
        user=user,
        is_completed=True
    ).count()

    total_hours = HourLog.objects.filter(
        goal__user=user
    ).aggregate(Sum('hours'))['hours__sum'] or 0

    current_goals = Goal.objects.filter(
        user=user
    ).exclude(
        status='COMPLETED'
    ).order_by('priority', 'target_date')

    users = User.objects.exclude(id=user_id).order_by('username')

    user_stats = []
    for u in users:
        user_completed_goals_count = Goal.objects.filter(
            user=u,
            status='COMPLETED'
        ).count()

        user_total_goals_count = Goal.objects.filter(
            user=u
        ).count()

        user_goals_completion_percentage = 0
        if user_total_goals_count > 0:
            user_goals_completion_percentage = int((user_completed_goals_count / user_total_goals_count) * 100)

        user_completed_tasks_count = UserTask.objects.filter(
            user=u,
            is_completed=True
        ).count()

        user_stats.append({
            'user': u,
            'completed_goals_count': user_completed_goals_count,
            'total_goals_count': user_total_goals_count,
            'goals_completion_percentage': user_goals_completion_percentage,
            'completed_tasks_count': user_completed_tasks_count,
            'is_current_user': u.id == request.user.id,
        })

    user_stats.sort(key=lambda x: x['goals_completion_percentage'], reverse=True)

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

        is_self = user.id == request.user.id

        try:
            goals = Goal.objects.filter(user=user)
            for goal in goals:
                Task.objects.filter(goal=goal).delete()
                Progress.objects.filter(goal=goal).delete()
                HourLog.objects.filter(goal=goal).delete()
                goal.delete()

            UserTask.objects.filter(user=user).delete()

            try:
                if hasattr(user, 'profile'):
                    user.profile.delete()
            except Profile.DoesNotExist:
                pass

            user.delete()

            if is_self:
                logout(request)
                messages.success(request, f'Your account has been deleted.')
                return redirect('dashboard')

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


@login_required
def task_completion_data(request):
    start_date = timezone.now().date() - timedelta(days=6)

    user_tasks = UserTask.objects.filter(
        user=request.user,
        is_completed=True,
        completed_date__isnull=False,
        completed_date__gte=start_date
    ).values('completed_date').annotate(count=Count('id'))

    goal_tasks = Task.objects.filter(
        goal__user=request.user,
        is_completed=True,
        completed_date__isnull=False,
        completed_date__gte=start_date
    ).values('completed_date').annotate(count=Count('id'))

    counts = {}
    for entry in user_tasks:
        counts[entry['completed_date']] = counts.get(entry['completed_date'], 0) + entry['count']
    for entry in goal_tasks:
        counts[entry['completed_date']] = counts.get(entry['completed_date'], 0) + entry['count']

    data = []
    current = start_date
    for _ in range(7):
        data.append({
            'date': current.strftime('%Y-%m-%d'),
            'count': counts.get(current, 0)
        })
        current += timedelta(days=1)

    return JsonResponse(data, safe=False)
