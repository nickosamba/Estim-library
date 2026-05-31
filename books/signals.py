from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from .models import Book
import threading
import sys

@receiver(post_save, sender=Book)
def auto_index_book(sender, instance, created, **kwargs):
    """
    Déclenche l'indexation IA en arrière-plan lors de la création/modification d'un livre.
    Désactivé pendant les tests pour éviter les verrous SQLite.
    """
    # Détection très robuste du mode test (Django injecte souvent 'test' dans sys.argv)
    is_test = 'test' in sys.argv or 'pytest' in sys.argv or 'test_coverage' in sys.argv
    
    # Évite aussi les commandes de gestion longues comme index_books
    is_mgmt = 'index_books' in sys.argv
    
    if is_test or is_mgmt:
        return
        
    # Ne pas indexer si les champs sont déjà remplis (évite le travail redondant)
    # sauf si on veut forcer la mise à jour, mais ici on privilégie la performance
    if instance.embedding and instance.extracted_text:
        return

    # Utilisation de on_commit pour éviter de bloquer la transaction en cours
    # et réduire les risques de 'database table is locked' avec SQLite
    transaction.on_commit(lambda: threading.Thread(
        target=instance.update_ai_index,
        name=f"AI-Index-{instance.id}",
        daemon=True
    ).start())
