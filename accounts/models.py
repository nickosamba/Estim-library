from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ('student', 'Étudiant'),
        ('teacher', 'Enseignant'),
        ('admin', 'Administrateur'),
    )

    CAMPUS_CHOICES = (
        ('brazzaville', 'Brazzaville'),
        ('pointe_noire', 'Pointe-Noire'),
        ('ouesso', 'Ouesso'),
    )

    DEPARTMENT_CHOICES = (
        ('sciences', 'Sciences et Technologies'),
        ('management', 'Management et Gestion'),
        ('lettres', 'Lettres et Sciences Humaines'),
    )

    LEVEL_CHOICES = (
        ('L1', 'Licence 1'),
        ('L2', 'Licence 2'),
        ('L3', 'Licence 3'),
        ('M1', 'Master 1'),
        ('M2', 'Master 2'),
        ('DOC', 'Doctorat'),
    )
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    campus = models.CharField(max_length=50, choices=CAMPUS_CHOICES, blank=True, null=True)
    department = models.CharField(max_length=50, choices=DEPARTMENT_CHOICES, blank=True, null=True)
    filiere = models.CharField(max_length=100, blank=True, null=True, help_text="Ex: Informatique, Droit, Marketing")
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, blank=True, null=True)
    
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('reservation_new', 'Nouvelle Réservation'),
        ('reservation_approved', 'Réservation Approuvée'),
        ('reservation_rejected', 'Réservation Refusée'),
        ('book_borrowed', 'Livre Emprunté'),
        ('book_returned', 'Livre Rendu'),
    )

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_notifications')
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    related_id = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} pour {self.recipient.username}"
