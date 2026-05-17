from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email', 'role', 'phone_number')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'block w-full px-4 py-3 border border-outline-variant rounded-xl shadow-sm focus:ring-2 focus:ring-primary-container focus:border-primary transition-all text-body-md bg-white'
            })


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('email', 'phone_number', 'bio', 'profile_picture')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'block w-full px-4 py-3 border border-outline-variant rounded-xl shadow-sm focus:ring-2 focus:ring-primary-container focus:border-primary transition-all text-body-md bg-surface-container-low'
            })
