import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_project.settings')
django.setup()

from books.models import Category, Author, Book, Campus

def seed_academic_books():
    print("Début de la génération des livres académiques...")
    
    # Ensure Campuses exist
    bzv = Campus.objects.get(code='BZV')
    pnr = Campus.objects.get(code='PNR')
    all_campus = Campus.objects.get(code='all')

    # Categories
    informatique, _ = Category.objects.get_or_create(name="Informatique")
    droit, _ = Category.objects.get_or_create(name="Droit & Sciences Politiques")
    management, _ = Category.objects.get_or_create(name="Management")

    # Authors
    author1, _ = Author.objects.get_or_create(name="Jean Dupont")
    author2, _ = Author.objects.get_or_create(name="Marie Silla")

    books_data = [
        {
            'title': "Algorithmes et Structures de Données",
            'isbn': "1111111111111",
            'category': informatique,
            'author': author1,
            'dept': 'sciences',
            'level': 'L1',
            'campuses': [bzv, pnr],
            'desc': "Un guide complet pour les débutants en informatique."
        },
        {
            'title': "Droit Civil au Congo",
            'isbn': "2222222222222",
            'category': droit,
            'author': author2,
            'dept': 'lettres',
            'level': 'L2',
            'campuses': [bzv],
            'desc': "Étude approfondie du code civil congolais."
        },
        {
            'title': "Marketing Stratégique",
            'isbn': "3333333333333",
            'category': management,
            'author': author1,
            'dept': 'management',
            'level': 'M1',
            'campuses': [all_campus],
            'desc': "Les clés pour réussir sa stratégie marketing en Afrique."
        },
        {
            'title': "Intelligence Artificielle Moderne",
            'isbn': "4444444444444",
            'category': informatique,
            'author': author2,
            'dept': 'sciences',
            'level': 'M2',
            'campuses': [pnr],
            'desc': "Introduction aux réseaux de neurones et au deep learning."
        }
    ]

    for data in books_data:
        book, created = Book.objects.get_or_create(
            isbn=data['isbn'],
            defaults={
                'title': data['title'],
                'category': data['category'],
                'author': data['author'],
                'target_department': data['dept'],
                'target_level': data['level'],
                'description': data['desc'],
                'publication_year': 2024,
                'is_available': True,
                'copies_available': 5
            }
        )
        if created:
            book.target_campuses.set(data['campuses'])
            print(f"Livre créé : {book.title}")
        else:
            print(f"Livre existant : {book.title}")

    print("Génération terminée !")

if __name__ == "__main__":
    seed_academic_books()
