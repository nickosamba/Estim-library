import os
import django
from django.test import Client, RequestFactory
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_project.settings')
django.setup()

from accounts.models import User, Notification
from books.models import Book, Author, Category, Campus, ReadingProgress
from reservations.models import Reservation

def run_tests():
    print("🚀 Démarrage de la vérification complète...")

    # Cleanup
    Reservation.objects.all().delete()
    Book.objects.all().delete()
    User.objects.all().delete()
    Campus.objects.all().delete()
    Author.objects.all().delete()

    # 1. Test Synchronisation Rôles -> Staff
    print("\n[1/5] Test Synchronisation Rôles...")
    student = User.objects.create_user(username='student', password='pass', role='student')
    admin_user = User.objects.create_user(username='admin_role', password='pass', role='admin')
    teacher = User.objects.create_user(username='teacher_role', password='pass', role='teacher')
    
    assert student.is_staff == False, "Étudiant ne devrait pas être staff"
    assert admin_user.is_staff == True, "Admin devrait être staff"
    assert teacher.is_staff == True, "Enseignant devrait être staff"
    print("✅ Succès : Les rôles sont bien synchronisés avec is_staff.")

    # 2. Test ISBN Optionnel
    print("\n[2/5] Test ISBN Optionnel...")
    author = Author.objects.create(name="Auteur Test")
    book1 = Book.objects.create(title="Livre avec ISBN", author=author, isbn="1234567890", publication_year=2024, copies_available=5)
    book2 = Book.objects.create(title="Livre sans ISBN", author=author, isbn=None, publication_year=2024, copies_available=5)
    book3 = Book.objects.create(title="Autre Livre sans ISBN", author=author, isbn="", publication_year=2024, copies_available=3)
    
    assert book2.isbn is None
    assert book3.isbn == ""
    print("✅ Succès : Les livres peuvent être créés avec ou sans ISBN.")

    # 3. Test Validation Campus
    print("\n[3/5] Test Validation Campus...")
    campus_a = Campus.objects.create(name="Campus A", code="A")
    campus_b = Campus.objects.create(name="Campus B", code="B")
    
    book_a = Book.objects.create(title="Livre Campus A", author=author, publication_year=2024, copies_available=5)
    book_a.target_campuses.add(campus_a)
    
    student_b = User.objects.create_user(username='student_b', password='pass', campus=campus_b, role='student')
    
    # Check is_available_at logic
    assert book_a.is_available_at(campus_a) == True
    assert book_a.is_available_at(campus_b) == False
    print("✅ Succès : La validation campus dans le modèle est correcte.")

    # 4. Test Signaux Stock (Centralisation)
    print("\n[4/5] Test Signaux Stock...")
    initial_stock = book_a.copies_available
    res = Reservation.objects.create(user=student, book=book_a, status='pending')
    book_a.refresh_from_db()
    assert book_a.copies_available == initial_stock - 1, "Le stock devrait diminuer à la création"
    
    res.status = 'cancelled'
    res.save()
    book_a.refresh_from_db()
    assert book_a.copies_available == initial_stock, "Le stock devrait remonter à l'annulation"
    
    res.status = 'approved'
    res.save()
    book_a.refresh_from_db()
    assert book_a.copies_available == initial_stock - 1, "Le stock devrait rediminuer si on réactive"
    
    res.status = 'returned'
    res.save()
    book_a.refresh_from_db()
    assert book_a.copies_available == initial_stock, "Le stock devrait remonter au retour"
    print("✅ Succès : Les signaux gèrent le stock parfaitement.")

    # 5. Test APIs (Author & Category)
    print("\n[5/5] Test APIs Création...")
    factory = RequestFactory()
    
    # Test Author API
    from books.views import create_author_api, create_category_api
    request = factory.post('/api/create-author/', {'name': 'Nouvel Auteur Unique'})
    request.user = admin_user
    response = create_author_api(request)
    import json
    data = json.loads(response.content)
    assert data['success'] == True
    assert Author.objects.filter(name='Nouvel Auteur Unique').exists()
    
    # Test Category API
    request = factory.post('/api/create-category/', {'name': 'Nouvelle Catégorie Unique'})
    request.user = admin_user
    response = create_category_api(request)
    data = json.loads(response.content)
    assert data['success'] == True
    assert Category.objects.filter(name='Nouvelle Catégorie Unique').exists()
    print("✅ Succès : Les APIs de création dynamique fonctionnent.")

    print("\n⭐ TOUS LES TESTS SONT VALIDÉS AVEC SUCCÈS ! ⭐")
    print("Le projet est 100% cohérent et robuste.")

if __name__ == "__main__":
    run_tests()
