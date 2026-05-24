from django.contrib import admin
from .models import Category, Author, Book, Review, Campus

@admin.register(Campus)
class CampusAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name', 'code')

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('book', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('book__title', 'user__username', 'comment')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'is_featured', 'is_available', 'copies_available')
    list_editable = ('is_featured', 'is_available', 'copies_available')
    list_filter = ('is_featured', 'category', 'is_available', 'publication_year')
    search_fields = ('title', 'isbn', 'author__name')
    prepopulated_fields = {'slug': ('title',)}
