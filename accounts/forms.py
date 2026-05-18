from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email', 'campus', 'department', 'filiere', 'level', 'phone_number')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from books.models import Campus
        
        # Customize campus field
        if 'campus' in self.fields:
            self.fields['campus'].queryset = Campus.objects.exclude(code='all')
            self.fields['campus'].label = "Campus de rattachement"
            self.fields['campus'].required = True
            self.fields['campus'].empty_label = "Sélectionnez votre campus"

        # Apply consistent styling to all fields
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'block w-full px-4 py-3 border border-outline-variant rounded-xl shadow-sm focus:ring-2 focus:ring-primary-container focus:border-primary transition-all text-body-md bg-white'
            })


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('email', 'phone_number', 'campus', 'department', 'filiere', 'level', 'bio', 'profile_picture')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from books.models import Campus
        
        # Customize campus field
        if 'campus' in self.fields:
            self.fields['campus'].queryset = Campus.objects.exclude(code='all')
            self.fields['campus'].label = "Campus de rattachement"
            self.fields['campus'].empty_label = "Sélectionnez votre campus"

        # Apply consistent styling
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'block w-full px-4 py-3 border border-outline-variant rounded-xl shadow-sm focus:ring-2 focus:ring-primary-container focus:border-primary transition-all text-body-md bg-surface-container-low'
            })
