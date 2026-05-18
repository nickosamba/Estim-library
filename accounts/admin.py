from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Informations Académiques', {'fields': ('role', 'campus', 'department', 'filiere', 'level')}),
        ('Informations Supplémentaires', {'fields': ('phone_number', 'bio', 'profile_picture')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informations Académiques', {'fields': ('role', 'campus', 'department', 'filiere', 'level')}),
        ('Informations Supplémentaires', {'fields': ('phone_number', 'bio', 'profile_picture')}),
    )
    list_display = ('username', 'email', 'role', 'campus', 'is_staff')
    list_filter = ('role', 'campus', 'is_staff', 'is_superuser')
