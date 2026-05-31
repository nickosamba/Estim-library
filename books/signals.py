from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Book
import threading

@receiver(post_save, sender=Book)
def auto_index_book(sender, instance, created, **kwargs):
    """
    Déclenche l'indexation IA en arrière-plan lors de la création/modification d'un livre.
    On utilise un thread pour ne pas bloquer l'interface admin.
    """
    # On ne lance l'indexation que si l'embedding est manquant ou si le texte a changé (simplifié)
    # Pour éviter les boucles infinies, update_ai_index utilise .update()
    thread = threading.Thread(target=instance.update_ai_index)
    thread.start()
