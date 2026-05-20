from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from books.models import Book
from .models import Reservation

def is_librarian(user):
    return user.is_authenticated and (user.role in ['admin', 'teacher'] or user.is_staff)

@login_required
def reserve_book(request, slug):
    book = get_object_or_404(Book, slug=slug)
    
    # Validation du Campus
    if request.user.campus and not book.is_available_at(request.user.campus):
        messages.error(request, f"Désolé, '{book.title}' n'est pas disponible sur votre campus ({request.user.campus.name}).")
        return redirect('books:book_detail', slug=slug)

    if book.copies_available <= 0:
        messages.error(request, f"Désolé, '{book.title}' n'est plus disponible en stock.")
        return redirect('books:book_detail', slug=slug)
    
    existing_reservation = Reservation.objects.filter(
        user=request.user, 
        book=book, 
        status__in=['pending', 'approved', 'borrowed']
    ).exists()
    
    if existing_reservation:
        messages.warning(request, "Vous avez déjà une réservation ou un emprunt en cours pour ce livre.")
        return redirect('books:book_detail', slug=slug)
    
    reservation = Reservation.objects.create(
        user=request.user,
        book=book,
        status='pending'
    )
    
    # La gestion du stock est maintenant gérée par les signaux (reservations/signals.py)

    # Notification pour le staff
    from accounts.models import User, Notification
    staff_members = User.objects.filter(role__in=['admin', 'teacher'])
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
    return redirect('profile')

@login_required
def cancel_reservation(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id, user=request.user)
    if reservation.status in ['pending', 'approved']:
        reservation.status = 'cancelled'
        reservation.save()
        # Le stock est géré par les signaux
        messages.success(request, "Réservation annulée.")
    return redirect('profile')

@login_required
def my_reservations(request):
    reservations = Reservation.objects.filter(user=request.user).order_by('-reserved_at')
    return render(request, 'reservations/my_reservations.html', {'reservations': reservations})

@login_required
@user_passes_test(is_librarian)
def member_list(request):
    from accounts.models import User
    members = User.objects.all().order_by('-date_joined')
    return render(request, 'reservations/member_list.html', {'members': members})

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

    # Count reservations per department
    dept_stats = reservations.values('user__department').annotate(
        count=Count('id')
    ).order_by('-count')
    
    dept_labels = dict(User.DEPARTMENT_CHOICES)
    formatted_dept_stats = [
        {'label': dept_labels.get(item['user__department'], 'Non défini'), 'value': item['count']}
        for item in dept_stats if item['user__department']
    ]

    # Count reservations per level
    level_stats = reservations.values('user__level').annotate(
        count=Count('id')
    ).order_by('-count')
    
    level_labels = dict(User.LEVEL_CHOICES)
    formatted_level_stats = [
        {'label': level_labels.get(item['user__level'], 'Non défini'), 'value': item['count']}
        for item in level_stats if item['user__level']
    ]

    context = {
        'reservations': reservations,
        'pending_count': pending_count,
        'borrowed_count': borrowed_count,
        'total_books': total_books,
        'late_count': late_count,
        'popular_books': popular_books,
        'dept_stats': formatted_dept_stats,
        'level_stats': formatted_level_stats,
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

    messages.success(request, f"Mise à jour réussie : {reservation.get_status_display()}")
    return redirect('reservations:librarian_dashboard')
