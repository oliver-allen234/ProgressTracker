from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from .models import Profile, Goal, Task, Progress, Training, TrainingAssignment

class ModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )

        self.profile = Profile.objects.create(
            user=self.user,
            bio='Test bio',
            birth_date=timezone.now().date() - timedelta(days=365*25)
        )

        self.goal = Goal.objects.create(
            user=self.user,
            title='Learn Django',
            description='Master Django web framework',
            priority='HIGH',
            status='IN_PROGRESS',
            start_date=timezone.now().date(),
            target_date=timezone.now().date() + timedelta(days=30)
        )

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

    def test_goal_creation(self):
        """Test that goal is created correctly"""
        self.assertEqual(Goal.objects.count(), 1)
        self.assertEqual(self.goal.__str__(), 'Learn Django')
        self.assertEqual(self.goal.priority, 'HIGH')
        self.assertEqual(self.goal.status, 'IN_PROGRESS')

    def test_task_creation(self):
        self.assertEqual(Task.objects.count(), 2)
        self.assertEqual(self.task1.__str__(), 'Complete Django tutorial')
        self.assertTrue(self.task1.is_completed)
        self.assertFalse(self.task2.is_completed)

    def test_progress_creation(self):
        self.assertEqual(Progress.objects.count(), 1)
        self.assertEqual(self.progress.value, 25.0)
        self.assertIn('Progress for Learn Django', self.progress.__str__())

    def test_goal_completion_percentage(self):
        self.assertEqual(self.goal.get_completion_percentage(), 50)

        self.task2.is_completed = True
        self.task2.save()

        self.assertEqual(self.goal.get_completion_percentage(), 100)

        new_goal = Goal.objects.create(
            user=self.user,
            title='Empty Goal',
            priority='LOW',
            status='NOT_STARTED'
        )
        self.assertEqual(new_goal.get_completion_percentage(), 0)


class TrainingModelTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(username='manager', password='pass', is_staff=True)
        self.user = User.objects.create_user(username='trainee', password='pass')
        self.training = Training.objects.create(
            title='Django Basics',
            description='Intro to Django',
            category='Web',
            estimated_hours=5,
            created_by=self.staff,
            is_active=True,
        )

    def test_training_str(self):
        self.assertEqual(str(self.training), 'Django Basics')

    def test_training_defaults(self):
        self.assertTrue(self.training.is_active)
        self.assertEqual(self.training.category, 'Web')

    def test_assignment_creation(self):
        assignment = TrainingAssignment.objects.create(
            training=self.training,
            trainee=self.user,
            assigned_by=self.staff,
            status='ASSIGNED',
        )
        self.assertEqual(assignment.status, 'ASSIGNED')
        self.assertEqual(assignment.trainee, self.user)
        self.assertEqual(assignment.training, self.training)

    def test_assignment_status_choices(self):
        assignment = TrainingAssignment.objects.create(
            training=self.training,
            trainee=self.user,
            assigned_by=self.staff,
            status='IN_PROGRESS',
        )
        assignment.status = 'COMPLETED'
        assignment.save()
        assignment.refresh_from_db()
        self.assertEqual(assignment.status, 'COMPLETED')


class TrainingViewAuthTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.staff = User.objects.create_user(username='manager', password='pass', is_staff=True)
        self.user = User.objects.create_user(username='trainee', password='pass')
        self.training = Training.objects.create(
            title='Test Module',
            description='desc',
            category='IT',
            estimated_hours=2,
            created_by=self.staff,
        )

    def test_training_list_requires_login(self):
        response = self.client.get(reverse('training-list'))
        self.assertRedirects(response, f'/login/?next={reverse("training-list")}')

    def test_training_list_accessible_to_all_logged_in(self):
        self.client.login(username='trainee', password='pass')
        response = self.client.get(reverse('training-list'))
        self.assertEqual(response.status_code, 200)

    def test_training_create_blocked_for_non_staff(self):
        self.client.login(username='trainee', password='pass')
        response = self.client.get(reverse('training-create'))
        self.assertEqual(response.status_code, 403)

    def test_training_create_accessible_to_staff(self):
        self.client.login(username='manager', password='pass')
        response = self.client.get(reverse('training-create'))
        self.assertEqual(response.status_code, 200)

    def test_training_delete_blocked_for_non_staff(self):
        self.client.login(username='trainee', password='pass')
        response = self.client.post(reverse('training-delete', args=[self.training.pk]))
        self.assertEqual(response.status_code, 403)

    def test_training_update_blocked_for_non_staff(self):
        self.client.login(username='trainee', password='pass')
        response = self.client.get(reverse('training-update', args=[self.training.pk]))
        self.assertEqual(response.status_code, 403)


class AssignmentAccessControlTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.staff = User.objects.create_user(username='manager', password='pass', is_staff=True)
        self.user1 = User.objects.create_user(username='user1', password='pass')
        self.user2 = User.objects.create_user(username='user2', password='pass')
        self.training = Training.objects.create(
            title='Security Training',
            description='desc',
            category='Security',
            estimated_hours=1,
            created_by=self.staff,
        )
        self.assignment = TrainingAssignment.objects.create(
            training=self.training,
            trainee=self.user1,
            assigned_by=self.staff,
            status='ASSIGNED',
        )

    def test_assignment_create_blocked_for_non_staff(self):
        self.client.login(username='user1', password='pass')
        response = self.client.get(reverse('assignment-create'))
        self.assertEqual(response.status_code, 403)

    def test_assignment_delete_blocked_for_non_staff(self):
        self.client.login(username='user1', password='pass')
        response = self.client.post(reverse('assignment-delete', args=[self.assignment.pk]))
        self.assertEqual(response.status_code, 403)

    def test_user_cannot_update_another_users_assignment(self):
        self.client.login(username='user2', password='pass')
        response = self.client.get(reverse('assignment-update', args=[self.assignment.pk]))
        self.assertEqual(response.status_code, 403)

    def test_trainee_can_update_own_assignment(self):
        self.client.login(username='user1', password='pass')
        response = self.client.get(reverse('assignment-update', args=[self.assignment.pk]))
        self.assertEqual(response.status_code, 200)

    def test_staff_can_update_any_assignment(self):
        self.client.login(username='manager', password='pass')
        response = self.client.get(reverse('assignment-update', args=[self.assignment.pk]))
        self.assertEqual(response.status_code, 200)

    def test_assignment_list_filters_for_regular_user(self):
        other_assignment = TrainingAssignment.objects.create(
            training=self.training,
            trainee=self.user2,
            assigned_by=self.staff,
            status='ASSIGNED',
        )
        self.client.login(username='user1', password='pass')
        response = self.client.get(reverse('assignment-list'))
        assignments = list(response.context['assignments'])
        self.assertIn(self.assignment, assignments)
        self.assertNotIn(other_assignment, assignments)

    def test_staff_sees_all_assignments(self):
        other_assignment = TrainingAssignment.objects.create(
            training=self.training,
            trainee=self.user2,
            assigned_by=self.staff,
            status='ASSIGNED',
        )
        self.client.login(username='manager', password='pass')
        response = self.client.get(reverse('assignment-list'))
        assignments = list(response.context['assignments'])
        self.assertIn(self.assignment, assignments)
        self.assertIn(other_assignment, assignments)
