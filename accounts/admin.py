from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Filiere
from .forms import CustomUserCreationForm

@admin.register(Filiere)
class FiliereAdmin(admin.ModelAdmin):
    list_display = ('name', 'department')
    list_filter = ('department',)
    search_fields = ('name',)

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    fieldsets = UserAdmin.fieldsets + (
        ('Informations Académiques', {'fields': ('role', 'campus', 'department', 'filiere', 'level')}),
        ('Informations Supplémentaires', {'fields': ('phone_number', 'bio', 'profile_picture')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    ) + (
        ('Informations Académiques', {'fields': ('role', 'campus', 'department', 'filiere', 'level')}),
        ('Informations Supplémentaires', {'fields': ('phone_number', 'bio', 'profile_picture')}),
    )
    list_display = ('username', 'email', 'role', 'campus', 'is_staff')
    list_filter = ('role', 'campus', 'is_staff', 'is_superuser')
