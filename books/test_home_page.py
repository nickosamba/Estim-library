from django.test import TestCase, Client
from django.urls import reverse
from books.models import Book, Author, Category, Campus, ReadingProgress
from accounts.models import User, Filiere

class HomePageFullTest(TestCase):
    def setUp(self):
        # Setup basic data
        self.campus = Campus.objects.create(name='Brazzaville', code='BZV')
        self.filiere = Filiere.objects.create(name='Sciences', department='sciences')
        self.author = Author.objects.create(name='Test Author')
        self.category = Category.objects.create(name='Test Category')
        
        # Create some books
        for i in range(5):
            Book.objects.create(
                title=f'Book {i}', author=self.author, category=self.category,
                isbn=f'ISBN-{i}', publication_year=2024, is_available=True
            )
            
        self.user = User.objects.create_user(
            username='tester', password='pass', email='test@test.com',
            campus=self.campus, filiere=self.filiere, level='L1'
        )

    def test_anonymous_access(self):
        """Test anonymous user access to home page."""
        response = self.client.get(reverse('books:book_list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_books'], 5)
        self.assertEqual(len(response.context['latest_books']), 5)
        self.assertEqual(len(response.context['reading_progress']), 0)

    def test_authenticated_recommendations(self):
        """Test recommendations for authenticated user."""
        # Create a specific book for user's campus
        target_book = Book.objects.create(
            title='Target Book', author=self.author, category=self.category,
            isbn='TARGET-ISBN', publication_year=2024, is_available=True,
            target_department='sciences'
        )
        target_book.target_campuses.add(self.campus)
        
        self.client.login(username='tester', password='pass')
        response = self.client.get(reverse('books:book_list'))
        
        recoms = response.context['recommendations']
        self.assertTrue(any(b.id == target_book.id for b in recoms))

    def test_reading_progress_display(self):
        """Test that reading progress shows up when user has history."""
        book = Book.objects.first()
        ReadingProgress.objects.create(user=self.user, book=book, last_page=10)
        
        self.client.login(username='tester', password='pass')
        response = self.client.get(reverse('books:book_list'))
        
        progress = response.context['reading_progress']
        self.assertEqual(len(progress), 1)
        self.assertEqual(progress[0].book.id, book.id)

    def test_treasure_fallback_logic(self):
        """Test the multi-step treasure selection logic."""
        # Case 1: Featured book
        featured_book = Book.objects.create(
            title='Featured', author=self.author, category=self.category,
            isbn='FEAT-ISBN', publication_year=2024, is_available=True,
            is_featured=True, cover_image='books/covers/test.jpg'
        )
        
        response = self.client.get(reverse('books:book_list'))
        self.assertEqual(response.context['treasure_of_the_month'].id, featured_book.id)
