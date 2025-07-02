from django.contrib import admin
from .models import Profile, Category, Goal, Task, Progress, UserTask, HourLog
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'birth_date')
    search_fields = ('user__username', 'user__email', 'bio')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'color')
    search_fields = ('name', 'description')

class TaskInline(admin.TabularInline):
    model = Task
    extra = 1

class ProgressInline(admin.TabularInline):
    model = Progress
    extra = 0

@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'priority', 'status', 'start_date', 'target_date')
    list_filter = ('status', 'priority', 'categories')
    search_fields = ('title', 'description', 'user__username')
    filter_horizontal = ('categories',)
    inlines = [TaskInline, ProgressInline]
    date_hierarchy = 'created_at'

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'goal', 'is_completed', 'due_date')
    list_filter = ('is_completed', 'due_date')
    search_fields = ('title', 'description', 'goal__title')

@admin.register(Progress)
class ProgressAdmin(admin.ModelAdmin):
    list_display = ('goal', 'date', 'value')
    list_filter = ('date',)
    search_fields = ('goal__title', 'note')
    date_hierarchy = 'date'

@admin.register(UserTask)
class UserTaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'status', 'priority', 'is_completed', 'due_date')
    list_filter = ('status', 'priority', 'is_completed', 'due_date')
    search_fields = ('title', 'description', 'user__username')
    date_hierarchy = 'created_at'

@admin.register(HourLog)
class HourLogAdmin(admin.ModelAdmin):
    list_display = ('goal', 'date', 'hours', 'description')
    list_filter = ('date', 'goal')
    search_fields = ('description', 'goal__title')
    date_hierarchy = 'date'
