import os
import django
import requests

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_project.settings')
django.setup()

from accounts.models import User
from books.models import Category
from django.http import HttpRequest
from books.views import fetch_book_info

def test_fetch_isbn(isbn):
    print(f"\n--- Testing ISBN: {isbn} ---")
    request = HttpRequest()
    request.GET = {'isbn': isbn}
    
    # Mocking user
    user = User.objects.filter(role='admin').first()
    if not user:
        user = User.objects.create_superuser('tempadmin', 'admin@example.com', 'pass', role='admin')
    request.user = user
    
    # We need to bypass the decorator or use the __wrapped__ attribute if available
    # but fetch_book_info is decorated multiple times.
    # Let's just call the underlying function logic if possible or just use a mock for decorators.
    
    # A trick to bypass decorators in tests:
    response = fetch_book_info.__original_view__(request) if hasattr(fetch_book_info, '__original_view__') else fetch_book_info(request)
    
    import json
    data = json.loads(response.content)
    print(json.dumps(data, indent=2))
    
    if data.get('success'):
        print(f"Title: {data.get('title')}")
        print(f"Category ID in DB: {data.get('category_id')}")
        print(f"Suggested Category from API: {data.get('suggested_category')}")
        
        if data.get('category_id'):
            cat = Category.objects.get(id=data.get('category_id'))
            print(f"Matched Category Name: {cat.name}")
        else:
            print("No match in DB, should show '+' button in UI if suggested_category is present.")

if __name__ == "__main__":
    test_fetch_isbn("9780132350884")
    test_fetch_isbn("9782070541270")
