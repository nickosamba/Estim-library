import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_project.settings')
django.setup()

from books.models import Campus

def seed_campuses():
    campuses = [
        {'name': 'Brazzaville', 'code': 'brazzaville'},
        {'name': 'Pointe-Noire', 'code': 'pointe_noire'},
        {'name': 'Ouesso', 'code': 'ouesso'},
        {'name': 'Tous les campus', 'code': 'all'},
    ]
    for c in campuses:
        campus, created = Campus.objects.get_or_create(code=c['code'], defaults={'name': c['name']})
        if created:
            print(f"Campus créé : {campus.name}")
        else:
            print(f"Campus existe déjà : {campus.name}")

if __name__ == "__main__":
    seed_campuses()
