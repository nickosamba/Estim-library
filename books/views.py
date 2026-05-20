from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import HttpResponse, JsonResponse
from .models import Book, Category, Favorite, ReadingProgress, Review, Bookmark, Annotation, Chapter, Campus
from .forms import ReviewForm, BookForm, AuthorForm
from django.db.models import Q
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
import requests
import re
import pandas as pd
import io

def book_list(request):
    query = request.GET.get('q')
    if query:
        books = Book.objects.filter(
            Q(title__icontains=query) | 
            Q(author__name__icontains=query) |
            Q(category__name__icontains=query),
            is_available=True
        )
    else:
        books = Book.objects.filter(is_available=True)
    
    latest_books = Book.objects.filter(is_available=True).order_by('-created_at')[:6]
    
    # Smart Recommendations based on user profile (Academic + Location)
    recommendations = Book.objects.none()
    if request.user.is_authenticated and request.user.role == 'student':
        user_campus_code = request.user.campus.code if request.user.campus else 'all'
        user_dept = request.user.department
        
        # 1. Perfect Match: Same Department AND (Same Campus OR All Campuses)
        if user_dept:
            recommendations = Book.objects.filter(
                is_available=True,
                target_department=user_dept,
                target_campuses__code__in=[user_campus_code, 'all']
            ).distinct().exclude(cover_image='').order_by('?')[:3]
            
            # 2. Fallback: Same Department, any Campus
            if not recommendations.exists():
                recommendations = Book.objects.filter(
                    is_available=True,
                    target_department=user_dept
                ).distinct().exclude(cover_image='').order_by('?')[:3]
        
        # 3. Last Fallback: Any available book (if no dept or no matches)
        if not recommendations.exists():
            recommendations = Book.objects.filter(is_available=True).distinct().exclude(cover_image='').order_by('?')[:3]
    else:
        # For non-authenticated or staff: General recommendations
        recommendations = Book.objects.filter(is_available=True).distinct().exclude(cover_image='').order_by('?')[:3]
    
    reading_progress = []
    if request.user.is_authenticated:
        reading_progress = ReadingProgress.objects.filter(user=request.user).order_by('-updated_at')[:3]
    
    context = {
        'books': books,
        'latest_books': latest_books,
        'recommendations': recommendations,
        'reading_progress': reading_progress,
        'search_query': query,
    }
    return render(request, 'books/book_list.html', context)

def book_detail(request, slug):
    book = get_object_or_404(Book, slug=slug)
    is_favorite = False
    if request.user.is_authenticated:
        is_favorite = Favorite.objects.filter(user=request.user, book=book).exists()
    
    reviews = book.reviews.all()
    user_review = None
    if request.user.is_authenticated:
        user_review = reviews.filter(user=request.user).first()
    
    form = ReviewForm(instance=user_review)
    
    # Check if book is local to user's campus
    is_local = True
    if request.user.is_authenticated:
        is_local = book.is_available_at(request.user.campus)
    
    context = {
        'book': book, 
        'is_favorite': is_favorite,
        'reviews': reviews,
        'user_review': user_review,
        'form': form,
        'is_local': is_local,
    }
    return render(request, 'books/book_detail.html', context)

@login_required
def add_review(request, slug):
    book = get_object_or_404(Book, slug=slug)
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            Review.objects.update_or_create(
                book=book, user=request.user,
                defaults={
                    'rating': form.cleaned_data['rating'],
                    'comment': form.cleaned_data['comment']
                }
            )
            if request.headers.get('HX-Request'):
                reviews = book.reviews.all()
                response = render(request, 'books/partials/review_list_partial.html', {'reviews': reviews, 'book': book})
                response['HX-Trigger'] = 'reviewAdded'
                return response
            
            messages.success(request, "Votre avis a été enregistré.")
        else:
            if request.headers.get('HX-Request'):
                return render(request, 'books/partials/review_list_partial.html', {
                    'reviews': book.reviews.all(), 
                    'book': book,
                    'error': "Veuillez sélectionner une note et écrire un commentaire."
                })
            messages.error(request, "Veuillez corriger les erreurs dans votre avis.")
            
    return redirect('books:book_detail', slug=slug)

@login_required
@user_passes_test(lambda u: u.role in ['admin', 'teacher'] or u.is_staff)
def export_books(request):
    format_type = request.GET.get('format', 'excel')
    books = Book.objects.all().values(
        'title', 'author__name', 'category__name', 'isbn', 
        'publication_year', 'copies_available', 'is_available'
    )
    df = pd.DataFrame(list(books))
    
    # Rename columns for better readability
    df.columns = ['Titre', 'Auteur', 'Catégorie', 'ISBN', 'Année', 'Stock', 'Disponible']
    
    if format_type == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="catalogue_estim_library.csv"'
        df.to_csv(path_or_buf=response, index=False, encoding='utf-8-sig')
    else:
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="catalogue_estim_library.xlsx"'
        with io.BytesIO() as buffer:
            df.to_excel(buffer, index=False, engine='openpyxl')
            response.write(buffer.getvalue())
            
    return response

@login_required
@user_passes_test(lambda u: u.role in ['admin', 'teacher'] or u.is_staff)
def import_books(request):
    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES['file']
        try:
            if file.name.endswith('.csv'):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file)
            
            from .models import Author
            count = 0
            for _, row in df.iterrows():
                # Flexible column mapping
                title = row.get('Titre') or row.get('title')
                author_name = row.get('Auteur') or row.get('author')
                category_name = row.get('Catégorie') or row.get('category')
                isbn = str(row.get('ISBN') or row.get('isbn') or '')
                year = row.get('Année') or row.get('year') or 2024
                stock = row.get('Stock') or row.get('copies') or 1
                
                if title and author_name:
                    author, _ = Author.objects.get_or_create(name=author_name)
                    category = None
                    if category_name:
                        category, _ = Category.objects.get_or_create(name=category_name)
                    
                    Book.objects.get_or_create(
                        title=title,
                        author=author,
                        defaults={
                            'category': category,
                            'isbn': isbn,
                            'publication_year': int(year),
                            'copies_available': int(stock),
                            'is_available': True
                        }
                    )
                    count += 1
            
            messages.success(request, f"Importation réussie : {count} ouvrages ajoutés ou mis à jour.")
        except Exception as e:
            messages.error(request, f"Erreur lors de l'importation : {str(e)}")
            
    return redirect('books:manage_books')

@login_required
@user_passes_test(lambda u: u.role in ['admin', 'teacher'] or u.is_staff)
def fetch_book_info(request):
    isbn = request.GET.get('isbn')
    if not isbn:
        return JsonResponse({'error': 'ISBN manquant'}, status=400)
    
    isbn = isbn.replace('-', '').replace(' ', '')
    
    # --- STEP 1: Try Google Books (Fast, but has quotas) ---
    google_url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
    try:
        response = requests.get(google_url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('totalItems', 0) > 0:
                volume_info = data['items'][0]['volumeInfo']
                title = volume_info.get('title', '')
                authors = volume_info.get('authors', [])
                author_name = authors[0] if authors else "Auteur Inconnu"
                description = volume_info.get('description', '')
                pub_date = volume_info.get('publishedDate', '')
                pub_year = pub_date[:4] if pub_date else 2024
                
                from .models import Author, Category
                author, _ = Author.objects.get_or_create(name=author_name)
                
                category_id = None
                category_name_found = ""
                categories = volume_info.get('categories', [])
                if categories:
                    category_name_found = categories[0]
                    matched_cat = Category.objects.filter(name__iexact=category_name_found).first()
                    if matched_cat:
                        category_id = matched_cat.id

                return JsonResponse({
                    'success': True,
                    'source': 'Google',
                    'title': title,
                    'author_id': author.id,
                    'author_name': author.name,
                    'description': description,
                    'publication_year': pub_year,
                    'category_id': category_id,
                    'suggested_category': category_name_found
                })
    except Exception:
        pass # Silently fail and try fallback

    # --- STEP 2: Fallback to Open Library (No quota, but can be slower) ---
    ol_url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&format=json&jscmd=data"
    try:
        response = requests.get(ol_url, timeout=15)
        if response.status_code == 200:
            data = response.json()
            bib_key = f'ISBN:{isbn}'
            if bib_key in data:
                book_data = data[bib_key]
                title = book_data.get('title', '')
                authors = book_data.get('authors', [])
                author_name = authors[0].get('name') if authors else "Auteur Inconnu"
                
                description = book_data.get('notes', '')
                category_name_found = ""
                if not description and 'subjects' in book_data:
                    subjects = [s.get('name') for s in book_data['subjects'][:5]]
                    category_name_found = subjects[0] if subjects else ""
                    description = "Sujets : " + ", ".join(subjects)
                
                pub_date = book_data.get('publish_date', '')
                import re
                year_match = re.search(r'\d{4}', pub_date)
                pub_year = year_match.group(0) if year_match else 2024
                
                from .models import Author, Category
                author, _ = Author.objects.get_or_create(name=author_name)
                
                category_id = None
                if category_name_found:
                    matched_cat = Category.objects.filter(name__iexact=category_name_found).first()
                    if matched_cat:
                        category_id = matched_cat.id

                return JsonResponse({
                    'success': True,
                    'source': 'OpenLibrary',
                    'title': title,
                    'author_id': author.id,
                    'author_name': author.name,
                    'description': description,
                    'publication_year': pub_year,
                    'category_id': category_id,
                    'suggested_category': category_name_found
                })
    except Exception as e:
        return JsonResponse({'success': False, 'error': f"Erreur de connexion (Google & OpenLibrary) : {str(e)}"})

    return JsonResponse({'success': False, 'error': 'Aucun livre trouvé pour cet ISBN sur aucune plateforme.'})

@login_required
@user_passes_test(lambda u: u.role in ['admin', 'teacher'] or u.is_staff)
def create_category_api(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            category, created = Category.objects.get_or_create(name=name)
            return JsonResponse({
                'success': True, 
                'id': category.id, 
                'name': category.name,
                'created': created
            })
    return JsonResponse({'success': False, 'error': 'Nom de catégorie manquant ou méthode invalide.'}, status=400)

@login_required
@user_passes_test(lambda u: u.role in ['admin', 'teacher'] or u.is_staff)
def manage_books(request):
    books = Book.objects.all().order_by('-created_at')
    return render(request, 'books/manage_books.html', {'books': books})

@login_required
@user_passes_test(lambda u: u.role in ['admin', 'teacher'] or u.is_staff)
def add_book(request):
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "L'ouvrage a été ajouté avec succès.")
            return redirect('books:manage_books')
    else:
        form = BookForm()
    return render(request, 'books/book_form.html', {'form': form, 'title': 'Ajouter un livre'})

@login_required
@user_passes_test(lambda u: u.role in ['admin', 'teacher'] or u.is_staff)
def edit_book(request, slug):
    book = get_object_or_404(Book, slug=slug)
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES, instance=book)
        if form.is_valid():
            form.save()
            messages.success(request, f"'{book.title}' a été mis à jour.")
            return redirect('books:manage_books')
    else:
        form = BookForm(instance=book)
    return render(request, 'books/book_form.html', {'form': form, 'title': 'Modifier le livre', 'book': book})

@login_required
def read_book(request, slug):
    book = get_object_or_404(Book, slug=slug)
    if not book.pdf_file:
        return redirect('books:book_detail', slug=slug)
    
    progress, _ = ReadingProgress.objects.get_or_create(user=request.user, book=book)
    chapters = book.chapters.all()
    bookmarks = Bookmark.objects.filter(user=request.user, book=book)
    annotations = Annotation.objects.filter(user=request.user, book=book)
    
    context = {
        'book': book, 
        'progress': progress,
        'chapters': chapters,
        'bookmarks': bookmarks,
        'annotations': annotations,
    }
    return render(request, 'books/read_book.html', context)

@login_required
def add_bookmark(request, slug):
    if request.method == 'POST':
        book = get_object_or_404(Book, slug=slug)
        page = request.POST.get('page')
        label = request.POST.get('label', '')
        if page:
            Bookmark.objects.create(user=request.user, book=book, page_number=page, label=label)
            messages.success(request, f"Marque-page ajouté à la page {page}.")
    return redirect('books:read_book', slug=slug)

@login_required
def delete_bookmark(request, bookmark_id):
    bookmark = get_object_or_404(Bookmark, id=bookmark_id, user=request.user)
    slug = bookmark.book.slug
    bookmark.delete()
    return redirect('books:read_book', slug=slug)

@login_required
def add_annotation(request, slug):
    if request.method == 'POST':
        book = get_object_or_404(Book, slug=slug)
        page = request.POST.get('page')
        content = request.POST.get('content')
        if page and content:
            Annotation.objects.create(user=request.user, book=book, page_number=page, content=content)
            messages.success(request, "Note enregistrée.")
    return redirect('books:read_book', slug=slug)

@login_required
def delete_annotation(request, annotation_id):
    annotation = get_object_or_404(Annotation, id=annotation_id, user=request.user)
    slug = annotation.book.slug
    annotation.delete()
    return redirect('books:read_book', slug=slug)

@login_required
def update_reading_progress(request, slug):
    if request.method == 'POST':
        page = request.POST.get('page')
        if page:
            book = get_object_or_404(Book, slug=slug)
            progress, _ = ReadingProgress.objects.get_or_create(user=request.user, book=book)
            progress.last_page = page
            progress.save()
            
            if request.headers.get('HX-Request') or request.headers.get('Accept') == 'application/json':
                return JsonResponse({'status': 'success', 'page': page})
                
            return redirect('books:read_book', slug=slug)
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def toggle_favorite(request, slug):
    book = get_object_or_404(Book, slug=slug)
    favorite, created = Favorite.objects.get_or_create(user=request.user, book=book)
    
    if not created:
        favorite.delete()
        messages.info(request, f"'{book.title}' a été retiré de vos favoris.")
    else:
        messages.success(request, f"'{book.title}' a été ajouté à vos favoris !")
        
    return redirect(request.META.get('HTTP_REFERER', reverse('books:book_list')))

def catalog(request):
    query = request.GET.get('q')
    category_id = request.GET.get('category')
    dept = request.GET.get('department')
    level = request.GET.get('level')
    campus_code = request.GET.get('campus')
    
    books = Book.objects.filter(is_available=True)
    
    if query:
        books = books.filter(
            Q(title__icontains=query) | 
            Q(author__name__icontains=query) |
            Q(description__icontains=query)
        )
    
    if category_id:
        books = books.filter(category_id=category_id)
        
    if dept:
        books = books.filter(target_department=dept)
        
    if level:
        books = books.filter(target_level=level)

    if campus_code:
        books = books.filter(Q(target_campuses__code=campus_code) | Q(target_campuses__code='all')).distinct()

    categories = Category.objects.all()
    campuses = Campus.objects.all()
    
    context = {
        'books': books,
        'categories': categories,
        'departments': Book.DEPARTMENT_CHOICES,
        'levels': Book.LEVEL_CHOICES,
        'campuses': campuses,
        'search_query': query,
        'selected_category': category_id,
        'selected_department': dept,
        'selected_level': level,
        'selected_campus': campus_code,
    }
    
    if request.headers.get('HX-Request'):
        return render(request, 'books/partials/book_list_partial.html', context)
        
    return render(request, 'books/catalog.html', context)
