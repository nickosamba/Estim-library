from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from books.models import Book
from .models import Reservation

def is_librarian(user):
    return user.is_authenticated and (user.role in ['admin', 'librarian'] or user.is_staff)

@login_required
def reserve_book(request, slug):
    book = get_object_or_404(Book, slug=slug)
    
    # Validation du Campus
    if not book.is_available_at(request.user.campus):
        if not request.user.campus:
            msg = "Profil incomplet (Campus)"
            messages.error(request, "Veuillez renseigner votre campus dans votre profil avant de réserver un ouvrage physique.")
        else:
            msg = "Campus différent"
            messages.error(request, f"Désolé, '{book.title}' n'est pas disponible sur votre campus ({request.user.campus.name}).")
        
        if request.headers.get('HX-Request'):
            return HttpResponse(f'<button disabled class="bg-error/10 text-error px-4 py-3 rounded-2xl font-bold text-[10px] uppercase tracking-tight opacity-80 cursor-default flex items-center justify-center gap-1"><span class="material-symbols-outlined text-sm">location_off</span> {msg}</button>')
        return redirect('books:book_detail', slug=slug)

    if book.copies_available <= 0:
        messages.error(request, f"Désolé, '{book.title}' n'est plus disponible en stock.")
        if request.headers.get('HX-Request'):
            return HttpResponse(f'<button disabled class="bg-error/10 text-error px-4 py-3 rounded-2xl font-bold text-[10px] uppercase tracking-tight opacity-80 cursor-default">Stock Épuisé</button>')
        return redirect('books:book_detail', slug=slug)
    
    existing_reservation = Reservation.objects.filter(
        user=request.user, 
        book=book, 
        status__in=['pending', 'approved', 'borrowed']
    ).exists()
    
    if existing_reservation:
        messages.warning(request, "Vous avez déjà une réservation ou un emprunt en cours pour ce livre.")
        if request.headers.get('HX-Request'):
            return HttpResponse(f'<button disabled class="bg-primary/10 text-primary px-4 py-3 rounded-2xl font-bold text-[10px] uppercase tracking-tight opacity-80 cursor-default flex items-center justify-center gap-1"><span class="material-symbols-outlined text-sm">info</span> Déjà réservé</button>')
        return redirect('books:book_detail', slug=slug)
    
    reservation = Reservation.objects.create(
        user=request.user,
        book=book,
        status='pending'
    )
    
    # La gestion du stock est maintenant gérée par les signaux (reservations/signals.py)

    # Notification pour le staff (bibliothécaires uniquement)
    from accounts.models import User, Notification
    staff_members = User.objects.filter(role='librarian')
    for staff in staff_members:
        Notification.objects.create(
            recipient=staff,
            sender=request.user,
            notification_type='reservation_new',
            title='Nouvelle Réservation',
            message=f"{request.user.username} a réservé '{book.title}'.",
            related_id=reservation.id
        )
    
    messages.success(request, f"La réservation pour '{book.title}' a été enregistrée.")
    
    if request.headers.get('HX-Request'):
        return HttpResponse(f'<button disabled class="bg-secondary/20 text-secondary px-6 py-3 rounded-2xl font-bold text-[11px] uppercase tracking-widest opacity-80 cursor-default flex items-center justify-center gap-2 animate-reveal-fade"><span class="material-symbols-outlined text-sm">check_circle</span> Réservé</button>')

    return redirect('profile')

@login_required
def cancel_reservation(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id, user=request.user)
    if reservation.status in ['pending', 'approved']:
        reservation.status = 'cancelled'
        reservation.save()
        # Le stock est géré par les signaux
        messages.success(request, "Réservation annulée.")
    
    if request.headers.get('HX-Request'):
        return HttpResponse("") # HTMX will remove the element
        
    return redirect('reservations:my_reservations')

@login_required
def my_reservations(request):
    all_reservations = Reservation.objects.filter(user=request.user).order_by('-reserved_at')

    current_reservations = all_reservations.filter(status__in=['pending', 'approved', 'borrowed'])
    past_reservations = all_reservations.filter(status__in=['returned', 'rejected', 'cancelled'])

    # Récupérer les progressions de lecture pour les badges
    from books.models import ReadingProgress
    progresses = ReadingProgress.objects.filter(user=request.user)
    # Créer un dictionnaire pour un accès facile dans le template : {book_id: last_page}
    progress_map = {p.book_id: p.last_page for p in progresses}

    context = {
        'current_reservations': current_reservations,
        'past_reservations': past_reservations,
        'today': timezone.now().date(),
        'progress_map': progress_map,
    }
    return render(request, 'reservations/my_reservations.html', context)
@login_required
@user_passes_test(is_librarian)
def member_list(request):
    from accounts.models import User
    from books.models import Campus
    from django.db.models import Count, Q, Exists, OuterRef
    
    # Base Queryset
    members = User.objects.all().order_by('-date_joined')
    
    # Filters
    query = request.GET.get('q')
    campus_id = request.GET.get('campus')
    dept = request.GET.get('department')
    
    if query:
        members = members.filter(
            Q(username__icontains=query) | 
            Q(email__icontains=query) |
            Q(filiere__name__icontains=query)
        )
    
    if campus_id:
        members = members.filter(campus_id=campus_id)
        
    if dept:
        members = members.filter(department=dept)

    # Annotate with late status
    today = timezone.now().date()
    overdue_reservations = Reservation.objects.filter(
        user=OuterRef('pk'),
        status='borrowed',
        end_date__lt=today
    )
    members = members.annotate(has_overdue=Exists(overdue_reservations))

    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(members, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'members': page_obj,
        'page_obj': page_obj,
        'campuses': Campus.objects.all(),
        'departments': User.DEPARTMENT_CHOICES,
        'search_query': query,
        'selected_campus': campus_id,
        'selected_department': dept,
    }

    if request.headers.get('HX-Request'):
        if request.headers.get('HX-Target') == 'members-container':
            return render(request, 'reservations/member_list.html', context)
        return render(request, 'reservations/partials/member_rows_partial.html', context)
        
    return render(request, 'reservations/member_list.html', context)

@login_required
@user_passes_test(lambda u: u.role == 'admin' or u.is_superuser)
def change_member_role(request, user_id):
    from accounts.models import User
    member = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        new_role = request.POST.get('role')
        if new_role in dict(User.ROLE_CHOICES):
            member.role = new_role
            # La mise à jour de is_staff est gérée par la méthode save() du modèle User
            member.save()
            messages.success(request, f"Le rôle de {member.username} a été mis à jour vers {member.get_role_display()}.")
    return redirect('reservations:member_list')

@login_required
@user_passes_test(is_librarian)
def librarian_dashboard(request):
    reservations = Reservation.objects.all().order_by('-reserved_at')
    pending_count = reservations.filter(status='pending').count()
    borrowed_count = reservations.filter(status='borrowed').count()
    total_books = Book.objects.count()

    # Gestion des retards
    today = timezone.now().date()
    late_reservations = reservations.filter(status='borrowed', end_date__lt=today)
    late_count = late_reservations.count()

    # Statistiques des livres les plus populaires (top 5)
    from django.db.models import Count
    popular_books = Book.objects.annotate(
        res_count=Count('reservations')
    ).order_by('-res_count')[:5]

    # Academic Analytics
    from accounts.models import User
    from django.db.models import Count
    import json

    # Count reservations per department
    dept_stats = reservations.values('user__department').annotate(
        count=Count('id')
    ).order_by('-count')
    
    dept_labels_dict = dict(User.DEPARTMENT_CHOICES)
    dept_data = {
        'labels': [dept_labels_dict.get(item['user__department'], 'Non défini') for item in dept_stats if item['user__department']],
        'values': [item['count'] for item in dept_stats if item['user__department']]
    }

    # Count reservations per level
    level_stats = reservations.values('user__level').annotate(
        count=Count('id')
    ).order_by('-count')
    
    level_labels_dict = dict(User.LEVEL_CHOICES)
    level_data = {
        'labels': [level_labels_dict.get(item['user__level'], 'Non défini') for item in level_stats if item['user__level']],
        'values': [item['count'] for item in level_stats if item['user__level']]
    }

    context = {
        'reservations': reservations,
        'pending_count': pending_count,
        'borrowed_count': borrowed_count,
        'total_books': total_books,
        'late_count': late_count,
        'popular_books': popular_books,
        'dept_data_json': json.dumps(dept_data),
        'level_data_json': json.dumps(level_data),
        'today': today,
    }
    return render(request, 'reservations/librarian_dashboard.html', context)


@login_required
@user_passes_test(is_librarian)
def update_reservation_status(request, reservation_id, new_status):
    reservation = get_object_or_404(Reservation, id=reservation_id)
    old_status = reservation.status
    
    if new_status == 'borrowed' and old_status != 'borrowed':
        reservation.start_date = timezone.now().date()
        reservation.end_date = timezone.now().date() + timedelta(days=14)
        
    reservation.status = new_status
    reservation.save()

    # Notification pour l'étudiant
    from accounts.models import Notification
    from django.core.mail import send_mail
    from django.conf import settings
    
    title = ""
    message = ""
    ntype = ""
    
    if new_status == 'approved':
        title = "Réservation Approuvée"
        message = f"Votre réservation pour '{reservation.book.title}' a été approuvée ! Vous pouvez venir le chercher."
        ntype = 'reservation_approved'
    elif new_status == 'rejected':
        title = "Réservation Refusée"
        message = f"Désolé, votre réservation pour '{reservation.book.title}' a été refusée."
        ntype = 'reservation_rejected'
    elif new_status == 'borrowed':
        title = "Livre Emprunté"
        message = f"Vous avez récupéré '{reservation.book.title}'. Date de retour prévue : {reservation.end_date.strftime('%d/%m/%Y')}."
        ntype = 'book_borrowed'
    elif new_status == 'returned':
        title = "Livre Rendu"
        message = f"Merci d'avoir rendu '{reservation.book.title}'."
        ntype = 'book_returned'

    if ntype:
        Notification.objects.create(
            recipient=reservation.user,
            sender=request.user,
            notification_type=ntype,
            title=title,
            message=message,
            related_id=reservation.id
        )
        
        # Envoi de l'email réel
        try:
            full_message = f"Bonjour {reservation.user.username},\n\n{message}\n\nL'équipe Estim Library."
            send_mail(
                f"[Estim Library] {title}",
                full_message,
                settings.DEFAULT_FROM_EMAIL,
                [reservation.user.email],
                fail_silently=True,
            )
        except Exception as e:
            print(f"Erreur envoi email: {e}")

    if request.headers.get('HX-Request'):
        response = render(request, 'reservations/partials/reservation_row.html', {
            'res': reservation,
            'today': timezone.now().date(),
            'user': request.user
        })
        response['HX-Trigger'] = 'updateStaffStats'
        return response

    messages.success(request, f"Mise à jour réussie : {reservation.get_status_display()}")
    return redirect('reservations:librarian_dashboard')

@login_required
@user_passes_test(is_librarian)
def get_staff_stats(request):
    reservations = Reservation.objects.all()
    pending_count = reservations.filter(status='pending').count()
    borrowed_count = reservations.filter(status='borrowed').count()
    total_books = Book.objects.count()
    today = timezone.now().date()
    late_count = reservations.filter(status='borrowed', end_date__lt=today).count()
    
    return render(request, 'reservations/partials/staff_stats_widgets.html', {
        'pending_count': pending_count,
        'borrowed_count': borrowed_count,
        'total_books': total_books,
        'late_count': late_count,
    })
