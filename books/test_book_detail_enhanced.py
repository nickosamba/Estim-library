from django.test import TestCase, Client
from django.urls import reverse
from books.models import Book, Category, Campus, Author, ReadingProgress
from accounts.models import User, Filiere
from reservations.models import Reservation

class BookDetailEnhancedTest(TestCase):
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
            title="Livre Principal",
            author=self.author,
            category=self.category,
            copies_available=5,
            is_available=True,
            publication_year=2024,
            isbn="1111111111111"
        )
        self.book.target_campuses.set([self.campus])
        
        # Livre similaire
        self.similar_book = Book.objects.create(
            title="Livre Similaire",
            author=self.author,
            category=self.category,
            copies_available=5,
            is_available=True,
            publication_year=2024,
            isbn="2222222222222"
        )

    def test_similar_books_display(self):
        """Vérifie que les ouvrages similaires sont présents dans le contexte."""
        self.client.login(username="student", password="pass")
        response = self.client.get(reverse('books:book_detail', kwargs={'slug': self.book.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertIn('similar_books', response.context)
        self.assertContains(response, "Livre Similaire")
        self.assertContains(response, "Ouvrages similaires")

    def test_reading_progress_badge(self):
        """Vérifie l'affichage du badge de progression de lecture."""
        # Création d'une progression
        ReadingProgress.objects.create(user=self.user, book=self.book, last_page=42)
        
        # Ajout fictif d'un fichier PDF pour voir le bouton
        self.book.pdf_file = "test.pdf"
        self.book.save()
        
        self.client.login(username="student", password="pass")
        response = self.client.get(reverse('books:book_detail', kwargs={'slug': self.book.slug}))
        
        self.assertContains(response, "Reprendre")
        self.assertContains(response, "PAGE 42")

    def test_htmx_reservation_on_detail_page(self):
        """Vérifie que la réservation HTMX fonctionne sur la page détail."""
        self.client.login(username="student", password="pass")
        url = reverse('reservations:reserve_book', kwargs={'slug': self.book.slug})
        
        response = self.client.get(url, HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        self.assertIn("Réservé", response.content.decode())

    def test_share_functionality_presence(self):
        """Vérifie la présence du script et du bouton de partage."""
        response = self.client.get(reverse('books:book_detail', kwargs={'slug': self.book.slug}))
        self.assertContains(response, "shareBook()")
        self.assertContains(response, "navigator.share")

    def test_mobile_responsiveness_classes(self):
        """Analyse structurelle des classes de réactivité mobile."""
        response = self.client.get(reverse('books:book_detail', kwargs={'slug': self.book.slug}))
        # Vérifie les classes responsive clés (sm:flex-row, sm:self-auto, etc.)
        self.assertContains(response, "sm:flex-row")
        self.assertContains(response, "sm:self-auto")
        self.assertContains(response, "grid-cols-2 sm:grid-cols-4") # Pour les livres similaires
