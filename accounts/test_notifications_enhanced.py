from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User, Notification

class NotificationsHTMXTest(TestCase):
    def setUp(self):
        self.client = Client()
        from books.models import Campus
        from accounts.models import Filiere
        self.campus = Campus.objects.create(name="Campus A", code="C1")
        self.filiere = Filiere.objects.create(name="Génie Logiciel", department="sciences")
        
        self.user = User.objects.create_user(
            username="testuser", 
            email="test@test.com", 
            password="pass",
            campus=self.campus,
            filiere=self.filiere,
            level="L3"
        )
        self.notif = Notification.objects.create(
            recipient=self.user,
            title="Test Notif",
            message="Contenu de test",
            notification_type="info",
            related_id=1
        )

    def test_mark_as_read_htmx(self):
        """Vérifie que marquer comme lu via HTMX renvoie les bons en-têtes et met à jour la base."""
        self.client.login(username="testuser", password="pass")
        url = reverse('mark_notification_as_read', kwargs={'notification_id': self.notif.id})
        
        response = self.client.get(url, HTTP_HX_REQUEST='true')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['HX-Trigger'], 'updateNotificationCount')
        
        self.notif.refresh_from_db()
        self.assertTrue(self.notif.is_read)

    def test_delete_notification_htmx(self):
        """Vérifie que la suppression via HTMX fonctionne."""
        self.client.login(username="testuser", password="pass")
        url = reverse('delete_notification', kwargs={'notification_id': self.notif.id})
        
        response = self.client.get(url, HTTP_HX_REQUEST='true')
        
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Notification.objects.filter(id=self.notif.id).exists())

    def test_api_unread_count(self):
        """Vérifie que l'API du compteur renvoie le bon fragment HTML."""
        self.client.login(username="testuser", password="pass")
        url = reverse('get_unread_notifications_count')
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("1", response.content.decode()) # Le compteur est à 1

    def test_activity_details_link(self):
        """Vérifie la présence du lien vers l'activité pour les étudiants."""
        self.client.login(username="testuser", password="pass")
        response = self.client.get(reverse('notifications_list'))
        self.assertContains(response, reverse('reservations:my_reservations'))

    def test_mobile_responsiveness_classes(self):
        """Vérifie les classes de réactivité mobile du centre de notifications."""
        self.client.login(username="testuser", password="pass")
        response = self.client.get(reverse('notifications_list'))
        # Vérifie l'empilement vertical sur petit écran
        self.assertContains(response, "flex-col sm:flex-row")
        self.assertContains(response, "sm:items-center")
