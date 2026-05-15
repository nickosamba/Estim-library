from django.contrib import admin
from .models import Reservation

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('user', 'book', 'reserved_at', 'status')
    list_filter = ('status', 'reserved_at')
    search_fields = ('user__username', 'book__title')
    actions = ['approve_reservation', 'mark_as_borrowed', 'mark_as_returned']

    def approve_reservation(self, request, queryset):
        queryset.update(status='approved')
    approve_reservation.short_description = "Approuver les réservations sélectionnées"

    def mark_as_borrowed(self, request, queryset):
        queryset.update(status='borrowed')
    mark_as_borrowed.short_description = "Marquer comme emprunté"

    def mark_as_returned(self, request, queryset):
        queryset.update(status='returned')
    mark_as_returned.short_description = "Marquer comme retourné"
