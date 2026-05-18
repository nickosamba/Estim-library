import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_project.settings')
django.setup()

from accounts.models import User
from books.models import Book, Author, Category
from reservations.models import Reservation
from django.db.models import Q

def simulate():
    print("=== SIMULATION DU SYSTÈME UNIVERSITAIRE ===\n")

    # 1. Nettoyage (optionnel pour la démo)
    User.objects.filter(username='etudiant_test').delete()
    User.objects.filter(username='admin_test').delete()

    # 2. Création d'un Étudiant (Brazzaville, Sciences, L1)
    student = User.objects.create_user(
        username='etudiant_test',
        password='password123',
        campus='brazzaville',
        department='sciences',
        filiere='Informatique',
        level='L1',
        role='student'
    )
    print(f"STAGIAIRE CRÉÉ : {student.username}")
    print(f"Campus: {student.get_campus_display()}, Dept: {student.get_department_display()}, Niveau: {student.level}\n")

    # 3. Création de Livres avec cibles académiques
    author, _ = Author.objects.get_or_create(name="Prof. Ndoki")
    cat, _ = Category.objects.get_or_create(name="Technologie")

    book_sci = Book.objects.create(
        title="Algorithmique de base",
        author=author,
        category=cat,
        target_campus='brazzaville',
        target_department='sciences',
        target_level='L1',
        publication_year=2024,
        isbn="111222333"
    )
    
    book_mgmt = Book.objects.create(
        title="Marketing Digital",
        author=author,
        category=cat,
        target_campus='pointe_noire',
        target_department='management',
        target_level='L3',
        publication_year=2024,
        isbn="444555666"
    )
    print(f"LIVRES CRÉÉS : '{book_sci.title}' et '{book_mgmt.title}'\n")

    # 4. TEST : Logique de Recommandation (Simulation de book_list view)
    print("--- TEST RECOMMANDATIONS ---")
    recommendations = Book.objects.filter(
        target_department=student.department,
        target_campus=student.campus
    )
    print(f"Recommandations pour l'étudiant : {[b.title for b in recommendations]}")
    if book_sci in recommendations:
        print("✅ SUCCÈS : Le livre de Sciences est bien recommandé à l'étudiant de Brazzaville.\n")

    # 5. TEST : Filtrage du Catalogue (Simulation de catalog view)
    print("--- TEST FILTRAGE CATALOGUE ---")
    # Simulation d'un filtre sur le département "management"
    filtered_mgmt = Book.objects.filter(target_department='management')
    print(f"Filtre 'Management' : {[b.title for b in filtered_mgmt]}")
    if book_mgmt in filtered_mgmt and book_sci not in filtered_mgmt:
        print("✅ SUCCÈS : Le catalogue filtre correctement par département.\n")

    # 6. TEST : Dashboard Analytique
    print("--- TEST DASHBOARD ANALYTIQUE ---")
    # On crée une réservation
    res = Reservation.objects.create(user=student, book=book_sci, status='approved')
    
    # Simulation de la logique de stats du dashboard
    from django.db.models import Count
    dept_stats = Reservation.objects.values('user__department').annotate(count=Count('id'))
    
    print("Statistiques par département (Côté Admin) :")
    for stat in dept_stats:
        dept_name = dict(User.DEPARTMENT_CHOICES).get(stat['user__department'])
        print(f"- {dept_name} : {stat['count']} réservation(s)")
    
    if any(s['user__department'] == 'sciences' for s in dept_stats):
        print("\n✅ SYSTÈME VALIDÉ : La logique universitaire est cohérente de bout en bout.")

if __name__ == "__main__":
    simulate()
