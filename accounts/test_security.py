from django.test import TestCase
from django.urls import reverse
from accounts.models import User, Filiere
from books.models import Campus
from accounts.forms import CustomUserCreationForm

class SecurityTests(TestCase):
    def setUp(self):
        # Create a campus and filiere for dynamic tests
        self.campus = Campus.objects.create(name='Brazzaville', code='BZV')
        self.filiere = Filiere.objects.create(name='Informatique', department='sciences')
        
        self.admin = User.objects.create_user(
            username='adminuser',
            password='adminpassword123',
            email='admin@test.com',
            campus=self.campus,
            filiere=self.filiere,
            level='DOC',
            role='admin',
            is_staff=True
        )
        self.teacher = User.objects.create_user(
            username='teacheruser',
            password='teacherpassword123',
            email='teacher@test.com',
            campus=self.campus,
            filiere=self.filiere,
            level='M2',
            role='teacher',
            is_staff=True
        )
        self.student = User.objects.create_user(
            username='studentuser',
            password='studentpassword123',
            email='student@test.com',
            campus=self.campus,
            filiere=self.filiere,
            level='L1',
            role='student'
        )

    def test_registration_form_no_role(self):
        """Verify that 'role' is not in the registration form fields."""
        form = CustomUserCreationForm()
        self.assertNotIn('role', form.fields)

    def test_registration_default_role_is_student(self):
        """Verify that a new user is always a student, even if someone tries to inject a role."""
        response = self.client.post(reverse('register'), {
            'username': 'hacker',
            'email': 'hacker@test.com',
            'password1': 'hackerpassword123',
            'password2': 'hackerpassword123',
            'role': 'admin',  # Attempting to inject role
            'campus': self.campus.id,
            'filiere': self.filiere.id,
            'level': 'L1'
        })
        self.assertEqual(response.status_code, 302)
        new_user = User.objects.get(username='hacker')
        self.assertEqual(new_user.role, 'student')

    def test_only_admin_can_change_role(self):
        """Verify that only 'admin' role can change roles, not 'teacher'."""
        # 1. Test Admin (Should work)
        self.client.login(username='adminuser', password='adminpassword123')
        response = self.client.post(reverse('reservations:change_member_role', args=[self.student.id]), {
            'role': 'teacher'
        })
        self.student.refresh_from_db()
        self.assertEqual(self.student.role, 'teacher')
        self.client.logout()

        # 2. Test Teacher (Should fail/redirect)
        self.client.login(username='teacheruser', password='teacherpassword123')
        response = self.client.post(reverse('reservations:change_member_role', args=[self.student.id]), {
            'role': 'admin'
        })
        # If user_passes_test fails, it redirects to login by default if not authorized
        # or stays as teacher if the post didn't go through
        self.student.refresh_from_db()
        self.assertNotEqual(self.student.role, 'admin')
