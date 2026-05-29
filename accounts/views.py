from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth import login
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Notification
from .forms import CustomUserCreationForm, ProfileUpdateForm, EmailAuthenticationForm

from django.urls import reverse

class CustomLoginView(auth_views.LoginView):
    authentication_form = EmailAuthenticationForm
    template_name = 'accounts/login.html'

    def get_success_url(self):
        user = self.request.user
        if user.role in ['admin', 'librarian'] or user.is_staff:
            return reverse('reservations:librarian_dashboard')
        return super().get_success_url()

    def form_valid(self, form):
        remember_me = form.cleaned_data.get('remember_me')
        if not remember_me:
            # La session expire à la fermeture du navigateur
            self.request.session.set_expiry(0)
            self.request.session.modified = True
        else:
            # La session dure 2 semaines (par défaut Django si non précisé, 
            # mais on peut forcer une durée ici ex: 1209600 secondes)
            self.request.session.set_expiry(1209600)
            self.request.session.modified = True
            
        return super().form_valid(form)

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # On spécifie le backend explicitement car il y en a plusieurs de configurés
            login(request, user, backend='accounts.backends.EmailOrUsernameBackend')
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
    
    # Statistiques de base
    returned_count = request.user.reservations.filter(status='returned').count()
    review_count = request.user.reviews.count()
    # Calcul du Score Culturel (10 pts par livre rendu, 5 pts par avis)
    cultural_score = (returned_count * 10) + (review_count * 5)

    # Limit to 5 most recent for display
    recent_reservations = request.user.reservations.all().order_by('-reserved_at')[:5]
    recent_favorites = request.user.favorites.all().order_by('-added_at')[:5]
    
    # Progression de lecture pour les badges
    from books.models import ReadingProgress
    progresses = ReadingProgress.objects.filter(user=request.user)
    progress_map = {p.book_id: p.last_page for p in progresses}

    context = {
        'form': form,
        'recent_reservations': recent_reservations,
        'recent_favorites': recent_favorites,
        'returned_count': returned_count,
        'cultural_score': cultural_score,
        'progress_map': progress_map,
    }

    # Add extra context for Staff Profile
    if request.user.role in ['admin', 'teacher'] or request.user.is_staff:
        from books.models import Book
        from reservations.models import Reservation
        from accounts.models import User
        context.update({
            'total_library_books': Book.objects.count(),
            'total_active_reservations': Reservation.objects.filter(status__in=['pending', 'approved', 'borrowed']).count(),
            'total_pending_requests': Reservation.objects.filter(status='pending').count(),
            'members_count': User.objects.count(),
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
    
    if request.headers.get('HX-Request'):
        response = HttpResponse("")
        response['HX-Trigger'] = 'updateNotificationCount'
        return response

    next_url = request.GET.get('next')
    if next_url == 'notifications_list':
        return redirect('notifications_list')
    return redirect('profile')

@login_required
def delete_notification(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.delete()
    
    if request.headers.get('HX-Request'):
        response = HttpResponse("")
        response['HX-Trigger'] = 'updateNotificationCount'
        return response

    next_url = request.GET.get('next')
    if next_url == 'notifications_list':
        return redirect('notifications_list')
    return redirect('profile')

@login_required
def clear_all_notifications(request):
    request.user.notifications.all().update(is_read=True)
    
    if request.headers.get('HX-Request'):
        response = HttpResponse("")
        response['HX-Trigger'] = 'updateNotificationCount'
        return response

    next_url = request.GET.get('next')
    if next_url == 'notifications_list':
        return redirect('notifications_list')
    return redirect('profile')

@login_required
def delete_all_notifications(request):
    request.user.notifications.all().delete()
    
    if request.headers.get('HX-Request'):
        response = HttpResponse("")
        response['HX-Trigger'] = 'updateNotificationCount'
        return response

    next_url = request.GET.get('next')
    if next_url == 'notifications_list':
        return redirect('notifications_list')
    return redirect('profile')

import google.generativeai as genai
import os
from django.conf import settings

@login_required
def chat_response(request):
    """
    Gère les réponses du chatbot avec mémoire de conversation et expertise métier.
    """
    from books.models import Book
    user_message = request.POST.get('message', '')
    
    # 1. Gestion de l'historique (Mémoire de session)
    if 'chat_history' not in request.session:
        request.session['chat_history'] = []
    
    history = request.session['chat_history']
    # On garde les 6 derniers messages (3 tours de dialogue) pour ne pas saturer le quota
    history = history[-6:]
    
    # 2. Préparation du contexte du catalogue (Recherche dynamique simplifiée)
    # On cherche les livres qui pourraient correspondre au message de l'utilisateur
    from django.db.models import Q
    search_terms = user_message.split()
    query = Q()
    for term in search_terms:
        if len(term) > 3:
            query |= Q(title__icontains=term) | Q(author__name__icontains=term) | Q(category__name__icontains=term)
    
    relevant_books = Book.objects.filter(is_available=True).filter(query).select_related('author', 'category')[:10]
    if not relevant_books:
        relevant_books = Book.objects.filter(is_available=True).select_related('author', 'category').order_by('?')[:5]
    
    # On inclut le lien relatif pour que l'IA puisse créer des ancres HTML
    books_context = "\n".join([f"- {b.title} par {b.author.name} (ID: {b.slug})" for b in relevant_books])
    
    # 3. Configuration de Gemini
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        bot_reply = "Désolé, l'assistant est en cours de maintenance (Clé API manquante)."
    else:
        try:
            genai.configure(api_key=api_key)
            models_to_try = ['gemini-2.0-flash', 'gemini-2.5-flash', 'gemini-2.0-flash-lite']
            response = None
            
            # 4. Prompt Système d'Expertise (Le "Manuel de la Bibliothèque")
            is_first_message = len(history) == 0
            system_instruction = f"""
            Tu es l'assistant EXPERT de 'Estim Library', à Brazzaville.
            Utilisateur : {request.user.username}. 
            
            CONNAISSANCES MÉTIER :
            - Prêts : 14 jours. PDF : Illimités. Inscription : Gratuite.
            - Campus : Brazzaville, Pointe-Noire.
            
            CATALOGUE ACTUEL (Pertinent pour la question) :
            {books_context}
            
            HISTORIQUE : {history}
            
            RÈGLES DE RÉPONSE CRITIQUES :
            1. {"Dis bonjour pour commencer la discussion." if is_first_message else "NE DIS PLUS BONJOUR."}
            2. Quand tu cites un livre du catalogue, crée TOUJOURS un lien HTML cliquable comme ceci : <a href='/book/ID/' class='text-primary underline font-bold'>Titre du livre</a> (Remplace ID par le slug fourni).
            3. Réponds de manière très concise.
            4. Si tu ne trouves pas le livre, dis-le poliment.
            """
            
            for model_name in models_to_try:
                try:
                    model = genai.GenerativeModel(model_name)
                    response = model.generate_content(f"{system_instruction}\n\nNouvelle question de l'utilisateur : {user_message}")
                    if response and response.text:
                        break
                except Exception as e:
                    print(f"Échec avec {model_name}: {str(e)[:50]}")
                    continue
            
            if response and response.text:
                bot_reply = response.text
                # Mise à jour de l'historique
                history.append(f"Utilisateur: {user_message}")
                history.append(f"Assistant: {bot_reply}")
                request.session['chat_history'] = history
                request.session.modified = True
            else:
                bot_reply = "Je suis un peu surchargé en ce moment. Réessayez dans quelques secondes !"
                
        except Exception as e:
            print(f"Erreur Gemini Globale: {e}")
            bot_reply = "Désolé, je rencontre une petite difficulté technique. Réessayez dans un instant !"
    
    return render(request, 'accounts/partials/chat_message.html', {
        'user_message': user_message,
        'bot_reply': bot_reply
    })

@login_required
def get_unread_notification_count(request):
    """Renvoie juste le nombre de notifications non lues pour HTMX."""
    count = request.user.notifications.filter(is_read=False).count()
    if count > 0:
        return HttpResponse(f'<span class="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-error text-[10px] font-bold text-white ring-2 ring-white animate-pulse">{count}</span>')
    return HttpResponse("")
