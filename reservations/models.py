from django.db import models
from django.conf import settings
from books.models import Book

class Reservation(models.Model):
    STATUS_CHOICES = (
        ('pending', 'En attente'),
        ('approved', 'Approuvée'),
        ('rejected', 'Refusée'),
        ('borrowed', 'Emprunté'),
        ('returned', 'Retourné'),
        ('cancelled', 'Annulée'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reservations')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reservations')
    reserved_at = models.DateTimeField(auto_now_add=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    rejection_reason = models.TextField(blank=True, null=True, verbose_name="Raison du refus")
    
    class Meta:
        ordering = ['-reserved_at']

    def __str__(self):
        return f"{self.user.username} - {self.book.title} ({self.get_status_display()})"
