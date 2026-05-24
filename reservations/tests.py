from django.test import TestCase
from django.urls import reverse
from .models import Reservation
from books.models import Book, Author, Campus
from accounts.models import User, Filiere
from django.utils import timezone
from datetime import timedelta

class ReservationsTests(TestCase):
    def setUp(self):
        self.campus = Campus.objects.create(name='Brazzaville', code='BZV')
        self.filiere = Filiere.objects.create(name='Sciences', department='sciences')
        self.user = User.objects.create_user(
            username='student', 
            password='pass', 
            role='student',
            email='student@test.com',
            campus=self.campus,
            filiere=self.filiere,
            level='L1'
        )
        self.staff = User.objects.create_user(
            username='staff', 
            password='pass', 
            role='admin',
            email='staff@test.com',
            campus=self.campus,
            filiere=self.filiere,
            level='DOC'
        )
        self.author = Author.objects.create(name='Author')
        self.book = Book.objects.create(title='Book', author=self.author, copies_available=2, is_available=True, slug='book', publication_year=2024)

    def test_reserve_book_success(self):
        self.client.login(username='student', password='pass')
        response = self.client.get(reverse('reservations:reserve_book', args=[self.book.slug]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Reservation.objects.count(), 1)
        self.book.refresh_from_db()
        self.assertEqual(self.book.copies_available, 1)

    def test_duplicate_reservation_prevention(self):
        self.client.login(username='student', password='pass')
        self.client.get(reverse('reservations:reserve_book', args=[self.book.slug]))
        # Try second time
        response = self.client.get(reverse('reservations:reserve_book', args=[self.book.slug]))
        self.assertEqual(Reservation.objects.count(), 1) # Still 1

    def test_staff_dashboard(self):
        self.client.login(username='staff', password='pass')
        response = self.client.get(reverse('reservations:librarian_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Gestion des Réservations")

    def test_update_status_and_notification(self):
        res = Reservation.objects.create(user=self.user, book=self.book, status='pending')
        self.client.login(username='staff', password='pass')
        response = self.client.get(reverse('reservations:update_reservation_status', args=[res.id, 'approved']))
        res.refresh_from_db()
        self.assertEqual(res.status, 'approved')
        # Check if notification was created for student
        self.assertEqual(self.user.notifications.count(), 1)
        self.assertEqual(self.user.notifications.first().notification_type, 'reservation_approved')
