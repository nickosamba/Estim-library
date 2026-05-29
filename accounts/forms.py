from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User

class EmailAuthenticationForm(AuthenticationForm):
    """
    Formulaire de connexion personnalisé acceptant l'email ou le username.
    """
    username = forms.CharField(
        label="Nom d'utilisateur ou Email",
        widget=forms.TextInput(attrs={
            'class': 'block w-full px-4 py-3 border border-outline-variant rounded-xl shadow-sm focus:ring-2 focus:ring-primary-container focus:border-primary transition-all text-body-md bg-white',
            'placeholder': "utilisateur@exemple.com ou pseudo"
        })
    )
    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={
            'class': 'block w-full px-4 py-3 border border-outline-variant rounded-xl shadow-sm focus:ring-2 focus:ring-primary-container focus:border-primary transition-all text-body-md bg-white',
        })
    )
    remember_me = forms.BooleanField(
        required=False,
        label="Se souvenir de moi",
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-primary border-outline-variant rounded focus:ring-primary transition-all cursor-pointer'
        })
    )


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email', 'campus', 'filiere', 'level')
        labels = {
            'username': "Nom d'utilisateur",
            'email': "Adresse e-mail",
            'filiere': "Filière / Spécialité",
            'level': "Niveau d'études",
        }
        help_texts = {
            'username': "Requis. 150 caractères ou moins. Lettres, chiffres et @/./+/-/_ uniquement.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from books.models import Campus
        
        # Email obligatoire
        if 'email' in self.fields:
            self.fields['email'].required = True

        # Traduction des labels et suppression des '----'
        if 'campus' in self.fields:
            self.fields['campus'].queryset = Campus.objects.exclude(code='all')
            self.fields['campus'].label = "Campus de rattachement"
            self.fields['campus'].required = True
            self.fields['campus'].empty_label = "Choisir un campus"

        # Les champs filiere et level ne sont plus forcés à True ici 
        # pour permettre la flexibilité selon le rôle (géré dans clean())
        if 'filiere' in self.fields:
            self.fields['filiere'].required = False # Sera vérifié dans clean()
            self.fields['filiere'].empty_label = "Choisir une filière"

        if 'level' in self.fields:
            self.fields['level'].required = False # Sera vérifié dans clean()
            choices = list(self.fields['level'].choices)
            if choices and choices[0][0] == '':
                choices[0] = ('', 'Choisir votre niveau')
                self.fields['level'].choices = choices

        # Traduction des champs de mot de passe (hérités de UserCreationForm)
        if 'password1' in self.fields:
            self.fields['password1'].label = "Mot de passe"
            self.fields['password1'].help_text = "Votre mot de passe doit contenir au moins 8 caractères, incluant des lettres et des chiffres."
        
        if 'password2' in self.fields:
            self.fields['password2'].label = "Confirmation du mot de passe"
            self.fields['password2'].help_text = "Veuillez saisir le même mot de passe pour confirmation."

        # Apply consistent styling to all fields
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'block w-full px-4 py-3 border border-outline-variant rounded-xl shadow-sm focus:ring-2 focus:ring-primary-container focus:border-primary transition-all text-body-md bg-white'
            })

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role', 'student') # Par défaut étudiant (inscription publique)
        filiere = cleaned_data.get('filiere')
        level = cleaned_data.get('level')

        # Validation conditionnelle : Obligatoire SEULEMENT pour les étudiants
        if role == 'student':
            if not filiere:
                self.add_error('filiere', "Ce champ est obligatoire pour les étudiants.")
            if not level:
                self.add_error('level', "Ce champ est obligatoire pour les étudiants.")
        
        return cleaned_data


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('email', 'phone_number', 'campus', 'filiere', 'level', 'bio', 'profile_picture')
        labels = {
            'email': "Adresse e-mail",
            'phone_number': "Numéro de téléphone",
            'filiere': "Filière / Spécialité",
            'level': "Niveau d'études",
            'bio': "Biographie",
            'profile_picture': "Photo de profil",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from books.models import Campus
        
        # Customize campus field
        if 'campus' in self.fields:
            self.fields['campus'].queryset = Campus.objects.exclude(code='all')
            self.fields['campus'].label = "Campus de rattachement"
            self.fields['campus'].empty_label = "Sélectionnez votre campus"

        if 'filiere' in self.fields:
            self.fields['filiere'].empty_label = "Choisir une filière"

        if 'level' in self.fields:
            choices = list(self.fields['level'].choices)
            if choices and choices[0][0] == '':
                choices[0] = ('', 'Choisir votre niveau')
                self.fields['level'].choices = choices

        # Apply premium styling
        premium_class = 'w-full bg-surface-container-low border-2 border-outline-variant/20 rounded-2xl px-5 py-3.5 font-bold text-on-surface focus:border-primary focus:ring-4 focus:ring-primary/5 transition-all outline-none'
        for field_name, field in self.fields.items():
            if field_name != 'profile_picture' and field_name != 'bio':
                field.widget.attrs.update({'class': premium_class})
            elif field_name == 'bio':
                field.widget.attrs.update({
                    'class': premium_class + ' min-h-[120px] resize-none',
                    'rows': 4
                })
            elif field_name == 'profile_picture':
                field.widget.attrs.update({
                    'class': 'block w-full text-sm text-outline file:mr-4 file:py-2.5 file:px-6 file:rounded-xl file:border-0 file:text-[10px] file:font-black file:uppercase file:tracking-widest file:bg-primary file:text-white hover:file:bg-primary/90 transition-all cursor-pointer'
                })
