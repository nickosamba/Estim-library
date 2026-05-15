from django.test import TestCase
from django.urls import reverse
from .models import Book, Author, Category
from accounts.models import User
import io
import pandas as pd

class BooksTests(TestCase):
    def setUp(self):
        self.author = Author.objects.create(name='Test Author')
        self.category = Category.objects.create(name='Test Category')
        self.book = Book.objects.create(
            title='Test Book',
            author=self.author,
            category=self.category,
            copies_available=5,
            is_available=True,
            slug='test-book',
            publication_year=2024
        )
        self.staff = User.objects.create_user(
            username='staffuser',
            password='staffpassword123',
            role='admin'
        )

    def test_book_list_view(self):
        response = self.client.get(reverse('books:book_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Book')

    def test_book_detail_view(self):
        response = self.client.get(reverse('books:book_detail', args=[self.book.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Book')

    def test_export_books_excel(self):
        self.client.login(username='staffuser', password='staffpassword123')
        response = self.client.get(reverse('books:export_books') + '?format=excel')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    def test_import_books_csv(self):
        self.client.login(username='staffuser', password='staffpassword123')
        csv_content = "Titre,Auteur,Catégorie,ISBN,Année,Stock\nImported Book,Imported Author,New Cat,123,2024,10"
        csv_file = io.BytesIO(csv_content.encode('utf-8-sig'))
        csv_file.name = 'test.csv'
        
        response = self.client.post(reverse('books:import_books'), {'file': csv_file})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Book.objects.filter(title='Imported Book').exists())
