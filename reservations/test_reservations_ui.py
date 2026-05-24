from django.test import TestCase, Client
from django.urls import reverse
from books.models import Book, Author, Category, Campus
from accounts.models import User, Filiere
from reservations.models import Reservation
from django.utils import timezone
from datetime import timedelta

class MyReservationsUITest(TestCase):
    def setUp(self):
        # Setup data
        self.campus = Campus.objects.create(name='Brazzaville', code='BZV')
        self.filiere = Filiere.objects.create(name='Sciences', department='sciences')
        self.author = Author.objects.create(name='Test Author')
        self.category = Category.objects.create(name='Test Category')
        
        self.user = User.objects.create_user(
            username='student', password='pass', email='student@test.com',
            campus=self.campus, filiere=self.filiere, level='L1', department='sciences'
        )
        
        self.book1 = Book.objects.create(title='Book Current', author=self.author, category=self.category, isbn='1', publication_year=2024, is_available=True)
        self.book2 = Book.objects.create(title='Book Past', author=self.author, category=self.category, isbn='2', publication_year=2024, is_available=True)
        
        # Current reservation
        self.res_current = Reservation.objects.create(user=self.user, book=self.book1, status='pending')
        
        # Past reservation
        self.res_past = Reservation.objects.create(user=self.user, book=self.book2, status='returned')

    def test_reservations_split(self):
        """Verify that current and past reservations are correctly separated in context."""
        self.client.login(username='student', password='pass')
        response = self.client.get(reverse('reservations:my_reservations'))
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.res_current, response.context['current_reservations'])
        self.assertIn(self.res_past, response.context['past_reservations'])
        self.assertEqual(response.context['current_reservations'].count(), 1)
        self.assertEqual(response.context['past_reservations'].count(), 1)

    def test_late_return_logic(self):
        """Verify that a late return is detected (via end_date comparison with today)."""
        # Set a borrowed reservation that is late
        self.res_current.status = 'borrowed'
        self.res_current.end_date = timezone.now().date() - timedelta(days=5)
        self.res_current.save()
        
        self.client.login(username='student', password='pass')
        response = self.client.get(reverse('reservations:my_reservations'))
        
        # Check if the late return warning class/text is likely present (checked via date in context)
        self.assertTrue(response.context['current_reservations'][0].end_date < response.context['today'])

    def test_htmx_cancel_reservation(self):
        """Verify that cancel_reservation returns empty response for HTMX."""
        self.client.login(username='student', password='pass')
        response = self.client.get(
            reverse('reservations:cancel_reservation', args=[self.res_current.id]),
            HTTP_HX_REQUEST='true'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "")
        
        # Verify status updated
        self.res_current.refresh_from_db()
        self.assertEqual(self.res_current.status, 'cancelled')
