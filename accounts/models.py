from django.contrib.auth.models import AbstractUser
from django.db import models

DEPARTMENT_CHOICES = (
    ('sciences', 'Sciences et Technologies'),
    ('management', 'Management et Gestion'),
    ('lettres', 'Lettres et Sciences Humaines'),
)

class Filiere(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nom de la filière")
    department = models.CharField(max_length=50, choices=DEPARTMENT_CHOICES, verbose_name="Département")

    class Meta:
        verbose_name = "Filière"
        verbose_name_plural = "Filières"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_department_display()})"

class User(AbstractUser):
    """
    Modèle utilisateur personnalisé pour Heritage Library.
    Gère les rôles (étudiant, bibliothécaire, admin), les campus et les cursus académiques.
    """
    ROLE_CHOICES = (
        ('student', 'Étudiant'),
        ('teacher', 'Enseignant'),
        ('librarian', 'Bibliothécaire'),
        ('admin', 'Administrateur'),
    )

    DEPARTMENT_CHOICES = DEPARTMENT_CHOICES

    LEVEL_CHOICES = (
        ('L1', 'Licence 1'),
        ('L2', 'Licence 2'),
        ('L3', 'Licence 3'),
        ('M1', 'Master 1'),
        ('M2', 'Master 2'),
        ('DOC', 'Doctorat'),
    )
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    email = models.EmailField(unique=True, blank=False, null=False, verbose_name="Adresse e-mail")
    campus = models.ForeignKey('books.Campus', on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Campus")
    department = models.CharField(max_length=50, choices=DEPARTMENT_CHOICES, blank=True, null=True)
    filiere = models.ForeignKey(Filiere, on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Filière")
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, blank=True, null=True, verbose_name="Niveau d'études")
    
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)

    def save(self, *args, **kwargs):
        """
        Surcharge de la méthode save pour automatiser certaines logiques :
        1. Validation des champs.
        2. Gestion stricte des accès staff (seul le superuser accède à /admin/).
        3. Assignation automatique du département via la filière choisie.
        """
        self.full_clean()
        
        # Sécurité : Seul le Superuser peut accéder à l'interface Django Admin
        if self.is_superuser:
            self.is_staff = True
            self.role = 'admin'
        else:
            # Pour tous les autres rôles, l'accès staff est révoqué par défaut
            self.is_staff = False
        
        # Automatisation du département pour éviter les erreurs de saisie
        if self.filiere:
            self.department = self.filiere.department
            
        super().save(*args, **kwargs)

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
