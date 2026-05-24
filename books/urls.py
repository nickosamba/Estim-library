from django.urls import path
from . import views

app_name = 'books'

urlpatterns = [
    path('', views.book_list, name='book_list'),
    path('sw.js', views.service_worker, name='service_worker'),
    path('catalog/', views.catalog, name='catalog'),
    path('book/<slug:slug>/', views.book_detail, name='book_detail'),
    path('book/<slug:slug>/read/', views.read_book, name='read_book'),
    path('book/<slug:slug>/read/progress/', views.update_reading_progress, name='update_reading_progress'),
    path('book/<slug:slug>/read/bookmark/add/', views.add_bookmark, name='add_bookmark'),
    path('read/bookmark/<int:bookmark_id>/delete/', views.delete_bookmark, name='delete_bookmark'),
    path('book/<slug:slug>/read/annotation/add/', views.add_annotation, name='add_annotation'),
    path('read/annotation/<int:annotation_id>/delete/', views.delete_annotation, name='delete_annotation'),
    path('book/<slug:slug>/favorite/', views.toggle_favorite, name='toggle_favorite'),
    path('book/<slug:slug>/review/', views.add_review, name='add_review'),
    path('manage/', views.manage_books, name='manage_books'),
    path('manage/add/', views.add_book, name='add_book'),
    path('manage/edit/<slug:slug>/', views.edit_book, name='edit_book'),
    path('manage/export/', views.export_books, name='export_books'),
    path('manage/import/', views.import_books, name='import_books'),
    path('manage/bulk-action/', views.bulk_action_books, name='bulk_action_books'),
    path('api/fetch-book-info/', views.fetch_book_info, name='fetch_book_info'),
    path('api/create-category/', views.create_category_api, name='create_category_api'),
    path('api/create-author/', views.create_author_api, name='create_author_api'),
]
