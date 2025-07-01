from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse

class Profile(models.Model):
    """
    Extension of the User model with a one-to-one relationship
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics', default='default.jpg')

    def __str__(self):
        return f'{self.user.username} Profile'

class Category(models.Model):
    """
    Categories for goals with a many-to-many relationship
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#007bff')  # Hex color code

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"

class Goal(models.Model):
    """
    Goals with a foreign key to User (one-to-many)
    and a many-to-many relationship with Category
    """
    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
    ]

    STATUS_CHOICES = [
        ('NOT_STARTED', 'Not Started'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('ON_HOLD', 'On Hold'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='goals')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NOT_STARTED')
    categories = models.ManyToManyField(Category, related_name='goals', blank=True)
    start_date = models.DateField(default=timezone.now)
    target_date = models.DateField(null=True, blank=True)
    completed_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('goal-detail', kwargs={'pk': self.pk})

    def get_completion_percentage(self):
        tasks = self.tasks.all()
        if not tasks:
            return 0
        completed_tasks = tasks.filter(is_completed=True).count()
        return int((completed_tasks / tasks.count()) * 100)

    def get_completed_tasks_count(self):
        """
        Get the number of completed tasks for this goal
        """
        return self.tasks.filter(is_completed=True).count()

    def get_total_tasks_count(self):
        """
        Get the total number of tasks for this goal
        """
        return self.tasks.count()

    def get_total_hours(self):
        """
        Calculate the total hours logged for this goal
        """
        from django.db.models import Sum
        result = self.hour_logs.aggregate(Sum('hours'))
        return result['hours__sum'] or 0

    def get_days_until_target(self):
        """
        Calculate the number of days remaining until the target date
        Returns:
            int: Number of days remaining (positive if target date is in the future, negative if in the past)
            None: If no target date is set
        """
        if not self.target_date:
            return None

        from django.utils import timezone
        today = timezone.now().date()
        delta = self.target_date - today
        return delta.days

    def get_target_date_status(self):
        """
        Get a status message based on how far the target date is
        """
        days = self.get_days_until_target()

        if days is None:
            return "No target date set"
        elif days < 0:
            return f"Overdue by {abs(days)} days"
        elif days == 0:
            return "Due today"
        elif days == 1:
            return "Due tomorrow"
        elif days <= 7:
            return f"Due in {days} days (this week)"
        elif days <= 30:
            return f"Due in {days} days (within a month)"
        else:
            return f"Due in {days} days"

class Task(models.Model):
    """
    Tasks with a foreign key to Goal (one-to-many)
    """
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_completed = models.BooleanField(default=False)
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['due_date', 'created_at']

class Progress(models.Model):
    """
    Progress updates with a foreign key to Goal (one-to-many)
    """
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE, related_name='progress_updates')
    date = models.DateField(default=timezone.now)
    note = models.TextField()
    value = models.FloatField(default=0)  # For numerical progress tracking

    def __str__(self):
        return f"Progress for {self.goal.title} on {self.date}"

    class Meta:
        verbose_name_plural = "Progress Updates"
        ordering = ['-date']

class HourLog(models.Model):
    """
    Hour logs with a foreign key to Goal (one-to-many)
    """
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE, related_name='hour_logs')
    date = models.DateField(default=timezone.now)
    hours = models.DecimalField(max_digits=5, decimal_places=2)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.hours} hours for {self.goal.title} on {self.date}"

    class Meta:
        ordering = ['-date']
        verbose_name = "Hour Log"
        verbose_name_plural = "Hour Logs"

class UserTask(models.Model):
    """
    Tasks with a direct foreign key to User (one-to-many)
    """
    STATUS_CHOICES = [
        ('TODO', 'To Do'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_tasks')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='TODO')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')
    is_completed = models.BooleanField(default=False)
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('user-task-detail', kwargs={'pk': self.pk})

    class Meta:
        ordering = ['due_date', 'priority', 'created_at']
