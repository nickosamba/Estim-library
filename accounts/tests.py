from django.test import TestCase
from django.urls import reverse
from .models import User, Notification, Filiere
from books.models import Campus

class AccountsTests(TestCase):
    def setUp(self):
        self.campus = Campus.objects.create(name='Brazzaville', code='BZV')
        self.filiere = Filiere.objects.create(name='Management', department='management')
        self.user = User.objects.create_user(
            username='teststudent',
            password='testpassword123',
            role='student',
            email='student@test.com',
            campus=self.campus,
            filiere=self.filiere,
            level='L1'
        )
        self.admin = User.objects.create_superuser(
            username='testadmin',
            password='adminpassword123',
            email='admin@test.com',
            campus=self.campus,
            filiere=self.filiere,
            level='DOC'
        )

    def test_login_view(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Estim Library")

    def test_registration(self):
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'new@test.com',
            'password1': 'newpassword123',
            'password2': 'newpassword123',
            'campus': self.campus.id,
            'filiere': self.filiere.id,
            'level': 'L1'
        })
        self.assertEqual(response.status_code, 302) # Redirect to book_list
        self.assertTrue(User.objects.filter(username='newuser').exists())
        self.assertEqual(User.objects.get(username='newuser').role, 'student')

    def test_notification_creation(self):
        notif = Notification.objects.create(
            recipient=self.user,
            title='Test Notif',
            message='Test message',
            notification_type='info'
        )
        self.assertEqual(self.user.notifications.count(), 1)
        self.assertFalse(notif.is_read)

    def test_mark_notif_read(self):
        notif = Notification.objects.create(
            recipient=self.user,
            title='Test Notif',
            message='Test message',
            notification_type='info'
        )
        self.client.login(username='teststudent', password='testpassword123')
        response = self.client.get(reverse('mark_notification_as_read', args=[notif.id]))
        notif.refresh_from_db()
        self.assertTrue(notif.is_read)
