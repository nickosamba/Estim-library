from django.core.management.base import BaseCommand
from accounts.models import User
from books.models import Book, Campus
from django.db import transaction

class Command(BaseCommand):
    help = 'Nettoie les doublons de campus et unifie les codes (BZV, PNR, OUE)'

    def handle(self, *args, **options):
        mapping = {
            'brazzaville': 'BZV',
            'pointe_noire': 'PNR',
            'pointe-noire': 'PNR',
            'ouesso': 'OUE'
        }

        self.stdout.write("Début du nettoyage...")
        
        with transaction.atomic():
            for old_code, new_code in mapping.items():
                old_campus = Campus.objects.filter(code=old_code).first()
                new_campus = Campus.objects.filter(code=new_code).first()
                
                if old_campus and new_campus and old_campus != new_campus:
                    self.stdout.write(f"Fusion de {old_code} vers {new_code}...")
                    
                    # 1. Update Users
                    users_count = User.objects.filter(campus=old_campus).update(campus=new_campus)
                    self.stdout.write(f"  - {users_count} utilisateurs mis à jour")
                    
                    # 2. Update Books (ManyToMany)
                    books = Book.objects.filter(target_campuses=old_campus)
                    for book in books:
                        book.target_campuses.remove(old_campus)
                        book.target_campuses.add(new_campus)
                    self.stdout.write(f"  - {books.count()} livres mis à jour")
                    
                    # 3. Delete Old Campus
                    old_campus.delete()
                    self.stdout.write(self.style.SUCCESS(f"  - Campus '{old_code}' supprimé"))

        self.stdout.write(self.style.SUCCESS("Nettoyage terminé avec succès !"))
