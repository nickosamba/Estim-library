import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_project.settings')
django.setup()

from accounts.models import User
from books.models import Book, Author, Campus, Category
from reservations.models import Reservation
from django.test import RequestFactory
from reservations.views import reserve_book
from django.contrib.messages.storage.fallback import FallbackStorage

def test_campus_validation():
    # Setup
    Campus.objects.all().delete()
    Book.objects.all().delete()
    User.objects.all().delete()
    
    campus_a = Campus.objects.create(name="Campus A", code="A")
    campus_b = Campus.objects.create(name="Campus B", code="B")
    
    author = Author.objects.create(name="Test Author")
    
    # Book restricted to Campus A
    book_a = Book.objects.create(
        title="Book A", 
        author=author, 
        copies_available=5, 
        is_available=True, 
        slug="book-a",
        publication_year=2024,
        isbn="1234567890"
    )
    book_a.target_campuses.add(campus_a)
    
    # User from Campus B
    user_b = User.objects.create_user(username="user_b", password="pass", campus=campus_b)
    
    print(f"User Campus: {user_b.campus}")
    print(f"Book A Target Campuses: {[c.name for c in book_a.target_campuses.all()]}")
    print(f"Is Book A available at Campus B? {book_a.is_available_at(campus_b)}")
    
    # Mock request
    factory = RequestFactory()
    request = factory.get(f'/reserve/{book_a.slug}/')
    request.user = user_b
    
    # Add messages support
    setattr(request, 'session', 'session')
    messages = FallbackStorage(request)
    setattr(request, '_messages', messages)
    
    # Case 2: Book with NO target campuses
    book_none = Book.objects.create(
        title="Book None", 
        author=author, 
        copies_available=5, 
        is_available=True, 
        slug="book-none",
        publication_year=2024,
        isbn="0987654321"
    )
    # No campuses added
    
    print(f"\nUser Campus: {user_b.campus}")
    print(f"Book None Target Campuses: {[c.name for c in book_none.target_campuses.all()]}")
    print(f"Is Book None available at Campus B? {book_none.is_available_at(campus_b)}")
    
    request_none = factory.get(f'/reserve/{book_none.slug}/')
    request_none.user = user_b
    setattr(request_none, 'session', 'session')
    setattr(request_none, '_messages', FallbackStorage(request_none))
    
    response_none = reserve_book(request_none, book_none.slug)
    reservation_none_exists = Reservation.objects.filter(user=user_b, book=book_none).exists()
    print(f"Reservation None created: {reservation_none_exists}")

if __name__ == "__main__":
    test_campus_validation()
