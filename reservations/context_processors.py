from .models import Reservation
from accounts.models import Notification

def pending_reservations_count(request):
    if request.user.is_authenticated:
        notifications = request.user.notifications.all().order_by('-created_at')
        context = {
            'unread_notifications_count': notifications.filter(is_read=False).count(),
            'recent_notifications': notifications[:5]
        }
        if request.user.role in ['admin', 'teacher'] or request.user.is_staff:
            context['pending_res_count'] = Reservation.objects.filter(status='pending').count()
        return context
    return {'pending_res_count': 0, 'unread_notifications_count': 0, 'recent_notifications': []}
