import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_project.settings')
django.setup()

from books.models import Category, Author, Book

def seed_data():
    print("Début du peuplement de la base de données...")

    # Création des catégories
    cat_it, _ = Category.objects.get_or_create(name="Informatique", description="Livres sur la programmation et les technologies.")
    cat_lit, _ = Category.objects.get_or_create(name="Littérature", description="Classiques et romans modernes.")
    cat_sci, _ = Category.objects.get_or_create(name="Sciences", description="Physique, Chimie et Mathématiques.")

    # Création des auteurs
    auth1, _ = Author.objects.get_or_create(name="Victor Hugo", biography="Célèbre écrivain français.")
    auth2, _ = Author.objects.get_or_create(name="Robert C. Martin", biography="Expert en génie logiciel, auteur de Clean Code.")
    auth3, _ = Author.objects.get_or_create(name="Albert Einstein", biography="Physicien théoricien.")

    # Création des livres
    books_data = [
        {
            "title": "Les Misérables",
            "author": auth1,
            "category": cat_lit,
            "description": "Un chef-d'œuvre de la littérature française.",
            "publication_year": 1862,
            "isbn": "9780140444308",
            "copies_available": 5
        },
        {
            "title": "Clean Code",
            "author": auth2,
            "category": cat_it,
            "description": "Un guide indispensable pour écrire du code propre et maintenable.",
            "publication_year": 2008,
            "isbn": "9780132350884",
            "copies_available": 3
        },
        {
            "title": "La Relativité",
            "author": auth3,
            "category": cat_sci,
            "description": "Explication simplifiée de la théorie de la relativité.",
            "publication_year": 1916,
            "isbn": "9782228882545",
            "copies_available": 2
        },
        {
            "title": "Python Crash Course",
            "author": auth2,
            "category": cat_it,
            "description": "Une introduction pratique à la programmation avec Python.",
            "publication_year": 2019,
            "isbn": "9781593279288",
            "copies_available": 10
        }
    ]

    for data in books_data:
        book, created = Book.objects.get_or_create(
            isbn=data["isbn"],
            defaults={
                "title": data["title"],
                "author": data["author"],
                "category": data["category"],
                "description": data["description"],
                "publication_year": data["publication_year"],
                "copies_available": data["copies_available"],
                "is_available": True
            }
        )
        if created:
            print(f"Livre créé : {book.title}")
        else:
            print(f"Livre déjà existant : {book.title}")

    print("Peuplement terminé avec succès !")

if __name__ == "__main__":
    seed_data()
