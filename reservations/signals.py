from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Reservation

@receiver(pre_save, sender=Reservation)
def handle_stock_on_status_change(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_reservation = Reservation.objects.get(pk=instance.pk)
            old_status = old_reservation.status
            new_status = instance.status
            book = instance.book

            # Statuts qui "libèrent" du stock
            return_stock_statuses = ['returned', 'rejected', 'cancelled']
            # Statuts qui "occupent" du stock
            reduce_stock_statuses = ['pending', 'approved', 'borrowed']

            if old_status in reduce_stock_statuses and new_status in return_stock_statuses:
                book.copies_available += 1
                if book.copies_available > 0:
                    book.is_available = True
                book.save()
            
            elif old_status in return_stock_statuses and new_status in reduce_stock_statuses:
                if book.copies_available > 0:
                    book.copies_available -= 1
                    if book.copies_available == 0:
                        book.is_available = False
                    book.save()
        except Reservation.DoesNotExist:
            pass

@receiver(post_save, sender=Reservation)
def handle_new_reservation_stock(sender, instance, created, **kwargs):
    if created:
        # Lors de la création d'une réservation (généralement 'pending')
        if instance.status in ['pending', 'approved', 'borrowed']:
            book = instance.book
            if book.copies_available > 0:
                book.copies_available -= 1
                if book.copies_available == 0:
                    book.is_available = False
                book.save()
