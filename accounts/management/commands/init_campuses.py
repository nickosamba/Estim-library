from django.core.management.base import BaseCommand
from books.models import Campus

class Command(BaseCommand):
    help = 'Initialise les campus par défaut dans la base de données'

    def handle(self, *args, **options):
        campuses = [
            {'name': 'Brazzaville', 'code': 'BZV'},
            {'name': 'Pointe-Noire', 'code': 'PNR'},
            {'name': 'Ouesso', 'code': 'OUE'},
            {'name': 'Tous les campus', 'code': 'all'},
        ]

        self.stdout.write("Initialisation des campus...")
        
        # Cleanup potential duplicates or old string codes
        old_codes = ['brazzaville', 'pointe_noire', 'ouesso']
        Campus.objects.filter(code__in=old_codes).delete()

        for data in campuses:
            campus, created = Campus.objects.get_or_create(
                code=data['code'],
                defaults={'name': data['name']}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Créé : {campus.name}"))
            else:
                self.stdout.write(f"Existe déjà : {campus.name}")
        
        self.stdout.write(self.style.SUCCESS("Opération terminée !"))
