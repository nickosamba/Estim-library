import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_project.settings')
django.setup()

from accounts.models import Filiere

def seed_filieres():
    filieres = [
        # Sciences
        {'name': 'Génie Informatique', 'department': 'sciences'},
        {'name': 'Génie Électrique', 'department': 'sciences'},
        {'name': 'Génie Civil', 'department': 'sciences'},
        {'name': 'Mathématiques', 'department': 'sciences'},
        # Management
        {'name': 'Marketing Digital', 'department': 'management'},
        {'name': 'Comptabilité et Finance', 'department': 'management'},
        {'name': 'Gestion des Ressources Humaines', 'department': 'management'},
        {'name': 'Audit et Contrôle de Gestion', 'department': 'management'},
        # Lettres
        {'name': 'Droit des Affaires', 'department': 'lettres'},
        {'name': 'Communication des Entreprises', 'department': 'lettres'},
        {'name': 'Sociologie', 'department': 'lettres'},
        {'name': 'Langues Étrangères', 'department': 'lettres'},
    ]

    print("Début de l'ajout des filières...")
    for f_data in filieres:
        filiere, created = Filiere.objects.get_or_create(
            name=f_data['name'],
            department=f_data['department']
        )
        if created:
            print(f"Filière créée : {filiere.name} ({filiere.get_department_display()})")
        else:
            print(f"Filière déjà existante : {filiere.name}")
    print("Terminé !")

if __name__ == "__main__":
    seed_filieres()
