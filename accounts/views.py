from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Notification
from .forms import CustomUserCreationForm, ProfileUpdateForm

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Bienvenue, {user.username} ! Votre compte a été créé avec succès.")
            return redirect('books:book_list')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})

@login_required
def profile(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Votre profil a été mis à jour avec succès !')
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=request.user)
    
    # Limit to 5 most recent for display
    recent_reservations = request.user.reservations.all().order_by('-reserved_at')[:5]
    recent_favorites = request.user.favorites.all().order_by('-added_at')[:5]
    
    context = {
        'form': form,
        'recent_reservations': recent_reservations,
        'recent_favorites': recent_favorites,
    }

    # Add extra context for Staff Profile
    if request.user.role in ['admin', 'teacher'] or request.user.is_staff:
        from books.models import Book
        from reservations.models import Reservation
        context.update({
            'total_library_books': Book.objects.count(),
            'total_active_reservations': Reservation.objects.filter(status__in=['pending', 'approved', 'borrowed']).count(),
            'total_pending_requests': Reservation.objects.filter(status='pending').count(),
        })
    
    return render(request, 'accounts/profile.html', context)

@login_required
def notifications_list(request):
    notifications = request.user.notifications.all().order_by('-created_at')
    return render(request, 'accounts/notifications.html', {'notifications': notifications})

@login_required
def mark_notification_as_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.is_read = True
    notification.save()
    
    next_url = request.GET.get('next')
    if next_url == 'notifications_list':
        return redirect('notifications_list')
    return redirect('profile')

@login_required
def delete_notification(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.delete()
    
    next_url = request.GET.get('next')
    if next_url == 'notifications_list':
        return redirect('notifications_list')
    return redirect('profile')

@login_required
def clear_all_notifications(request):
    request.user.notifications.all().update(is_read=True)
    
    next_url = request.GET.get('next')
    if next_url == 'notifications_list':
        return redirect('notifications_list')
    return redirect('profile')

@login_required
def delete_all_notifications(request):
    request.user.notifications.all().delete()
    
    next_url = request.GET.get('next')
    if next_url == 'notifications_list':
        return redirect('notifications_list')
    return redirect('profile')
