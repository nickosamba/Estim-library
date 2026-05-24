from django.test import TestCase, Client
from django.urls import reverse
from books.models import Book, Category, Campus, Author
from accounts.models import User
from reservations.models import Reservation

class CatalogBehaviorTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.campus1 = Campus.objects.create(name="Campus A", code="C1")
        self.campus2 = Campus.objects.create(name="Campus B", code="C2")
        self.author = Author.objects.create(name="Auteur Test")
        self.category = Category.objects.create(name="Informatique")
        
        from accounts.models import Filiere
        self.filiere = Filiere.objects.create(name="Génie Logiciel", department="sciences")
        
        self.user = User.objects.create_user(
            username="student", 
            email="student@test.com", 
            password="pass",
            campus=self.campus1,
            filiere=self.filiere,
            level="L3"
        )
        
        self.book1 = Book.objects.create(
            title="Livre Local",
            author=self.author,
            category=self.category,
            copies_available=5,
            is_available=True,
            publication_year=2024,
            isbn="1234567890123",
            target_department="sciences"
        )
        self.book1.target_campuses.set([self.campus1])
        
        self.book2 = Book.objects.create(
            title="Livre Distant",
            author=self.author,
            category=self.category,
            copies_available=5,
            is_available=True,
            publication_year=2024,
            isbn="9876543210987"
        )
        self.book2.target_campuses.set([self.campus2])

    def test_catalog_access_and_filtering(self):
        """Vérifie que le catalogue s'affiche et filtre correctement."""
        self.client.login(username="student", password="pass")
        response = self.client.get(reverse('books:catalog'))
        self.assertEqual(response.status_code, 200)
        # Par défaut, un étudiant connecté voit les livres de son campus (Livre Local)
        self.assertContains(response, "Livre Local")
        
    def test_reservation_htmx_success(self):
        """Vérifie le succès d'une réservation via HTMX."""
        self.client.login(username="student", password="pass")
        url = reverse('reservations:reserve_book', kwargs={'slug': self.book1.slug})
        
        # Simulation d'une requête HTMX
        response = self.client.get(url, HTTP_HX_REQUEST='true')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("Réservé", response.content.decode())
        self.assertTrue(Reservation.objects.filter(user=self.user, book=self.book1).exists())

    def test_reservation_htmx_wrong_campus(self):
        """Vérifie le message d'erreur HTMX pour un campus différent."""
        self.client.login(username="student", password="pass")
        url = reverse('reservations:reserve_book', kwargs={'slug': self.book2.slug})
        
        # Requête HTMX sur un livre qui n'est pas sur le campus de l'étudiant
        response = self.client.get(url, HTTP_HX_REQUEST='true')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("Campus différent", response.content.decode())
        self.assertFalse(Reservation.objects.filter(user=self.user, book=self.book2).exists())

    def test_reservation_htmx_already_reserved(self):
        """Vérifie le message HTMX si le livre est déjà réservé par l'utilisateur."""
        Reservation.objects.create(user=self.user, book=self.book1, status='pending')
        
        self.client.login(username="student", password="pass")
        url = reverse('reservations:reserve_book', kwargs={'slug': self.book1.slug})
        
        response = self.client.get(url, HTTP_HX_REQUEST='true')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("Déjà réservé", response.content.decode())
