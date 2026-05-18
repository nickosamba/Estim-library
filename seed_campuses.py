import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_project.settings')
django.setup()

from books.models import Campus

def seed_campuses():
    campuses = [
        {'name': 'Brazzaville', 'code': 'BZV'},
        {'name': 'Pointe-Noire', 'code': 'PNR'},
        {'name': 'Ouesso', 'code': 'OUE'},
        {'name': 'Tous les campus', 'code': 'all'},
    ]

    print("Début de l'ajout des campus...")
    for campus_data in campuses:
        campus, created = Campus.objects.get_or_create(
            code=campus_data['code'],
            defaults={'name': campus_data['name']}
        )
        if created:
            print(f"Campus créé : {campus.name} ({campus.code})")
        else:
            print(f"Campus déjà existant : {campus.name}")
    print("Terminé !")

if __name__ == "__main__":
    seed_campuses()
