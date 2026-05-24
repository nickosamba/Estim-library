from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User, Filiere
from books.models import Book, Category, Campus, ReadingProgress, Review, Author
from reservations.models import Reservation

class ProfileEnhancedTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.campus = Campus.objects.create(name="Campus A", code="C1")
        self.author = Author.objects.create(name="Auteur Test")
        self.category = Category.objects.create(name="Informatique")
        self.filiere = Filiere.objects.create(name="Génie Logiciel", department="sciences")
        
        self.user = User.objects.create_user(
            username="testuser", 
            email="test@test.com", 
            password="pass",
            campus=self.campus,
            filiere=self.filiere,
            level="L3"
        )
        
        # Création de quelques données pour les stats
        self.book = Book.objects.create(
            title="Livre Test",
            author=self.author,
            category=self.category,
            publication_year=2024,
            isbn="1111111111111"
        )
        
        # 1 livre rendu
        Reservation.objects.create(user=self.user, book=self.book, status='returned')
        # 1 avis posté
        Review.objects.create(user=self.user, book=self.book, rating=5, comment="Super")
        # 1 progression de lecture
        ReadingProgress.objects.create(user=self.user, book=self.book, last_page=25)

    def test_profile_dynamic_stats(self):
        """Vérifie le calcul dynamique du score culturel et des emprunts."""
        self.client.login(username="testuser", password="pass")
        response = self.client.get(reverse('profile'))
        
        self.assertEqual(response.status_code, 200)
        # Score culturel : (1 rendu * 10) + (1 avis * 5) = 15
        self.assertEqual(response.context['cultural_score'], 15)
        self.assertEqual(response.context['returned_count'], 1)
        self.assertContains(response, "15") # Score affiché
        self.assertContains(response, "1")  # Emprunts finis affichés

    def test_reading_progress_on_profile(self):
        """Vérifie l'affichage du badge de progression dans les activités récentes."""
        self.client.login(username="testuser", password="pass")
        response = self.client.get(reverse('profile'))
        
        self.assertContains(response, "P. 25")

    def test_staff_extra_context(self):
        """Vérifie les compteurs supplémentaires pour le staff."""
        self.user.role = 'admin'
        self.user.save()
        
        self.client.login(username="testuser", password="pass")
        response = self.client.get(reverse('profile'))
        
        self.assertIn('members_count', response.context)
        self.assertEqual(response.context['members_count'], 1)
        self.assertContains(response, "Gestion Membres")

    def test_modal_form_styling_classes(self):
        """Vérifie la présence des classes de styling premium dans le modal."""
        self.client.login(username="testuser", password="pass")
        response = self.client.get(reverse('profile'))
        
        # Vérifie les classes custom appliquées dans le template
        self.assertContains(response, "bg-surface-container-low border-2 border-outline-variant/20")
        self.assertContains(response, "focus:border-primary focus:ring-4")

    def test_profile_mobile_responsiveness(self):
        """Vérifie les classes de réactivité du profil."""
        self.client.login(username="testuser", password="pass")
        response = self.client.get(reverse('profile'))
        
        self.assertContains(response, "flex-col md:flex-row") # Header
        self.assertContains(response, "grid-cols-1 md:grid-cols-2") # Info grid
        self.assertContains(response, "grid-cols-1 md:grid-cols-3") # Stats/Actions
