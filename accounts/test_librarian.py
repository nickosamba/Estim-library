from django.test import TestCase
from django.urls import reverse
from accounts.models import User, Filiere
from books.models import Campus, Book, Author

class LibrarianRoleTests(TestCase):
    def setUp(self):
        self.campus = Campus.objects.create(name='Brazzaville', code='BZV')
        self.filiere = Filiere.objects.create(name='Sciences', department='sciences')
        
        self.librarian = User.objects.create_user(
            username='librarian',
            password='pass',
            email='lib@test.com',
            campus=self.campus,
            filiere=self.filiere,
            level='DOC',
            role='librarian'
        )
        self.teacher = User.objects.create_user(
            username='teacher',
            password='pass',
            email='teacher@test.com',
            campus=self.campus,
            filiere=self.filiere,
            level='M2',
            role='teacher'
        )
        self.student = User.objects.create_user(
            username='student',
            password='pass',
            email='student@test.com',
            campus=self.campus,
            filiere=self.filiere,
            level='L1',
            role='student'
        )
        self.author = Author.objects.create(name='Author')
        self.book = Book.objects.create(title='Book', author=self.author, copies_available=2, is_available=True, slug='book', publication_year=2024)

    def test_librarian_access_dashboard(self):
        """Librarian should be able to access the dashboard."""
        self.client.login(username='librarian', password='pass')
        response = self.client.get(reverse('reservations:librarian_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_teacher_no_access_dashboard(self):
        """Teacher should NOT be able to access the dashboard anymore."""
        self.client.login(username='teacher', password='pass')
        response = self.client.get(reverse('reservations:librarian_dashboard'))
        # Should redirect to login (default behavior of user_passes_test)
        self.assertEqual(response.status_code, 302)

    def test_librarian_can_manage_books(self):
        """Librarian should be able to access manage_books view."""
        self.client.login(username='librarian', password='pass')
        response = self.client.get(reverse('books:manage_books'))
        self.assertEqual(response.status_code, 200)

    def test_librarian_receive_notification(self):
        """Librarian should receive notification when a student reserves a book."""
        self.client.login(username='student', password='pass')
        self.client.get(reverse('reservations:reserve_book', args=[self.book.slug]))
        
        self.assertEqual(self.librarian.notifications.count(), 1)
        self.assertEqual(self.teacher.notifications.count(), 0)
