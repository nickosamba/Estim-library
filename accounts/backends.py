from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()

class EmailOrUsernameBackend(ModelBackend):
    """
    Backend d'authentification personnalisé permettant de se connecter
    soit avec le nom d'utilisateur (username) soit avec l'adresse e-mail.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)
        
        try:
            # Recherche par username ou email
            user = User.objects.get(Q(username=username) | Q(email=username))
        except User.DoesNotExist:
            # Exécuter le hachage pour éviter les attaques par analyse temporelle
            User().set_password(password)
            return None
        except User.MultipleObjectsReturned:
            # Si par erreur plusieurs utilisateurs ont le même email
            return User.objects.filter(Q(username=username) | Q(email=username)).order_by('id').first()

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
