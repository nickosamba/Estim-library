from django.urls import path
from . import views

app_name = 'reservations'

urlpatterns = [
    path('my-reservations/', views.my_reservations, name='my_reservations'),
    path('reserve/<slug:slug>/', views.reserve_book, name='reserve_book'),
    path('cancel/<int:reservation_id>/', views.cancel_reservation, name='cancel_reservation'),
    path('manage/', views.librarian_dashboard, name='librarian_dashboard'),
    path('members/', views.member_list, name='member_list'),
    path('members/change-role/<int:user_id>/', views.change_member_role, name='change_member_role'),
    path('update-status/<int:reservation_id>/<str:new_status>/', views.update_reservation_status, name='update_reservation_status'),
    path('api/stats/', views.get_staff_stats, name='get_staff_stats'),
]
