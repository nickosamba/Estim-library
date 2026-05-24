from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from books.models import Book, Category, Campus, Author, ReadingProgress
from accounts.models import User, Filiere
from reservations.models import Reservation

class ReservationsUIFinalTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.campus = Campus.objects.create(name="Campus A", code="C1")
        self.author = Author.objects.create(name="Auteur Test")
        self.category = Category.objects.create(name="Informatique")
        self.filiere = Filiere.objects.create(name="Génie Logiciel", department="sciences")
        
        self.user = User.objects.create_user(
            username="student", 
            email="student@test.com", 
            password="pass",
            campus=self.campus,
            filiere=self.filiere,
            level="L3"
        )
        
        self.book = Book.objects.create(
            title="Livre Test",
            author=self.author,
            category=self.category,
            copies_available=5,
            is_available=True,
            publication_year=2024,
            isbn="1234567890123"
        )
        self.book.target_campuses.set([self.campus])

    def test_reservation_badges_and_progress(self):
        """Vérifie l'affichage des badges de progression et du bouton Reprendre."""
        # Créer une réservation empruntée
        res = Reservation.objects.create(
            user=self.user, 
            book=self.book, 
            status='borrowed',
            end_date=timezone.now().date() + timedelta(days=7)
        )
        # Créer une progression
        ReadingProgress.objects.create(user=self.user, book=self.book, last_page=15)
        self.book.pdf_file = "test.pdf"
        self.book.save()

        self.client.login(username="student", password="pass")
        response = self.client.get(reverse('reservations:my_reservations'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "PAGE 15")
        self.assertContains(response, "Reprendre")
        self.assertContains(response, "À rendre au Campus Campus A")

    def test_late_alert_badge(self):
        """Vérifie l'affichage du badge Retard Critique."""
        Reservation.objects.create(
            user=self.user, 
            book=self.book, 
            status='borrowed',
            end_date=timezone.now().date() - timedelta(days=1) # Retard d'un jour
        )

        self.client.login(username="student", password="pass")
        response = self.client.get(reverse('reservations:my_reservations'))
        
        self.assertContains(response, "Retard Critique")
        self.assertContains(response, "animate-pulse")

    def test_rejection_reason_display(self):
        """Vérifie que la raison du refus s'affiche dans l'historique."""
        Reservation.objects.create(
            user=self.user, 
            book=self.book, 
            status='rejected',
            rejection_reason="Livre réservé pour maintenance"
        )

        self.client.login(username="student", password="pass")
        response = self.client.get(reverse('reservations:my_reservations'))
        
        self.assertContains(response, "Motif du refus")
        self.assertContains(response, "Livre réservé pour maintenance")

    def test_empty_state_cta(self):
        """Vérifie la présence du bouton Explorer le catalogue si vide."""
        self.client.login(username="student", password="pass")
        response = self.client.get(reverse('reservations:my_reservations'))
        
        self.assertContains(response, "Aucune réservation active")
        self.assertContains(response, "Explorer le catalogue")

    def test_mobile_responsiveness_classes(self):
        """Vérifie les classes de réactivité mobile pour les réservations."""
        # Créer une réservation pour avoir une carte à analyser
        Reservation.objects.create(user=self.user, book=self.book, status='pending')
        
        self.client.login(username="student", password="pass")
        response = self.client.get(reverse('reservations:my_reservations'))
        
        self.assertContains(response, "flex-col md:flex-row")
        self.assertContains(response, "text-center md:text-left")
        self.assertContains(response, "md:flex-col") # Pour les boutons d'action
