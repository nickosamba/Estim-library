from django import forms
from .models import Book, Author, Category, Review

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.HiddenInput(),
            'comment': forms.Textarea(attrs={
                'class': 'w-full p-4 rounded-2xl border border-outline-variant/30 focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all resize-none',
                'placeholder': 'Partagez votre avis sur cet ouvrage...',
                'rows': 4
            }),
        }

class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = [
            'title', 'author', 'category', 'target_department', 'target_level', 
            'target_filiere', 'description', 'isbn', 'publication_year', 
            'copies_available', 'cover_image', 'pdf_file', 'is_available'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'w-full p-4 rounded-2xl border border-outline-variant/30 focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all'}),
            'author': forms.Select(attrs={'class': 'w-full p-4 rounded-2xl border border-outline-variant/30 focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all'}),
            'category': forms.Select(attrs={'class': 'w-full p-4 rounded-2xl border border-outline-variant/30 focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all'}),
            'target_department': forms.Select(attrs={'class': 'w-full p-4 rounded-2xl border border-outline-variant/30 focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all'}),
            'target_level': forms.Select(attrs={'class': 'w-full p-4 rounded-2xl border border-outline-variant/30 focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all'}),
            'target_filiere': forms.TextInput(attrs={'class': 'w-full p-4 rounded-2xl border border-outline-variant/30 focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all', 'placeholder': 'Ex: Informatique, Droit'}),
            'description': forms.Textarea(attrs={'class': 'w-full p-4 rounded-2xl border border-outline-variant/30 focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all', 'rows': 4}),
            'isbn': forms.TextInput(attrs={'class': 'w-full p-4 rounded-2xl border border-outline-variant/30 focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all'}),
            'publication_year': forms.NumberInput(attrs={'class': 'w-full p-4 rounded-2xl border border-outline-variant/30 focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all'}),
            'copies_available': forms.NumberInput(attrs={'class': 'w-full p-4 rounded-2xl border border-outline-variant/30 focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'w-6 h-6 text-primary rounded-lg border-outline-variant/30 focus:ring-primary'}),
        }

class AuthorForm(forms.ModelForm):
    class Meta:
        model = Author
        fields = ['name', 'biography']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full p-4 rounded-2xl border border-outline-variant/30 focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all'}),
            'biography': forms.Textarea(attrs={'class': 'w-full p-4 rounded-2xl border border-outline-variant/30 focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all', 'rows': 3}),
        }
