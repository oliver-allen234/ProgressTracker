from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from .models import Profile, Category, Goal, Task, Progress

# Create your tests here.
class ModelTests(TestCase):
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )

        # Create profile for test user
        self.profile = Profile.objects.create(
            user=self.user,
            bio='Test bio',
            birth_date=timezone.now().date() - timedelta(days=365*25)  # 25 years ago
        )

        # Create categories
        self.category1 = Category.objects.create(
            name='Work',
            description='Work-related goals',
            color='#ff0000'
        )

        self.category2 = Category.objects.create(
            name='Health',
            description='Health and fitness goals',
            color='#00ff00'
        )

        # Create a goal
        self.goal = Goal.objects.create(
            user=self.user,
            title='Learn Django',
            description='Master Django web framework',
            priority='HIGH',
            status='IN_PROGRESS',
            start_date=timezone.now().date(),
            target_date=timezone.now().date() + timedelta(days=30)
        )

        # Add categories to goal
        self.goal.categories.add(self.category1)

        # Create tasks for the goal
        self.task1 = Task.objects.create(
            goal=self.goal,
            title='Complete Django tutorial',
            description='Go through the official Django tutorial',
            is_completed=True,
            due_date=timezone.now().date() + timedelta(days=7)
        )

        self.task2 = Task.objects.create(
            goal=self.goal,
            title='Build a project',
            description='Create a real-world Django project',
            is_completed=False,
            due_date=timezone.now().date() + timedelta(days=14)
        )

        # Create progress update for the goal
        self.progress = Progress.objects.create(
            goal=self.goal,
            date=timezone.now().date(),
            note='Started working on the tutorial',
            value=25.0
        )

    def test_profile_creation(self):
        """Test that profile is created correctly"""
        self.assertEqual(self.profile.user.username, 'testuser')
        self.assertEqual(self.profile.__str__(), 'testuser Profile')

    def test_category_creation(self):
        """Test that categories are created correctly"""
        self.assertEqual(Category.objects.count(), 2)
        self.assertEqual(self.category1.__str__(), 'Work')
        self.assertEqual(self.category2.color, '#00ff00')

    def test_goal_creation(self):
        """Test that goal is created correctly"""
        self.assertEqual(Goal.objects.count(), 1)
        self.assertEqual(self.goal.__str__(), 'Learn Django')
        self.assertEqual(self.goal.priority, 'HIGH')
        self.assertEqual(self.goal.status, 'IN_PROGRESS')

    def test_goal_category_relationship(self):
        """Test the many-to-many relationship between goals and categories"""
        self.assertEqual(self.goal.categories.count(), 1)
        self.assertEqual(self.goal.categories.first(), self.category1)

        # Add another category
        self.goal.categories.add(self.category2)
        self.assertEqual(self.goal.categories.count(), 2)

        # Test reverse relationship
        self.assertEqual(self.category1.goals.count(), 1)
        self.assertEqual(self.category1.goals.first(), self.goal)

    def test_task_creation(self):
        """Test that tasks are created correctly"""
        self.assertEqual(Task.objects.count(), 2)
        self.assertEqual(self.task1.__str__(), 'Complete Django tutorial')
        self.assertTrue(self.task1.is_completed)
        self.assertFalse(self.task2.is_completed)

    def test_progress_creation(self):
        """Test that progress updates are created correctly"""
        self.assertEqual(Progress.objects.count(), 1)
        self.assertEqual(self.progress.value, 25.0)
        self.assertIn('Progress for Learn Django', self.progress.__str__())

    def test_goal_completion_percentage(self):
        """Test the get_completion_percentage method"""
        # 1 out of 2 tasks completed = 50%
        self.assertEqual(self.goal.get_completion_percentage(), 50)

        # Complete the second task
        self.task2.is_completed = True
        self.task2.save()

        # Now should be 100%
        self.assertEqual(self.goal.get_completion_percentage(), 100)

        # Test with no tasks
        new_goal = Goal.objects.create(
            user=self.user,
            title='Empty Goal',
            priority='LOW',
            status='NOT_STARTED'
        )
        self.assertEqual(new_goal.get_completion_percentage(), 0)
