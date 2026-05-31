from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth import login
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Notification
from .forms import CustomUserCreationForm, ProfileUpdateForm, EmailAuthenticationForm

from django.urls import reverse
import json

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

from django.http import StreamingHttpResponse, HttpResponse
import time

# --- LOGIQUE DU CHATBOT SUPER-INTELLIGENT ---

def get_chatbot_tools(request):
    """Définit les fonctions que l'IA peut appeler."""
    from books.models import Book, Category
    from reservations.models import Reservation
    from .models import UserPreference
    import numpy as np

    def reserve_book(book_id: int):
        """Réserve un livre pour l'utilisateur actuel. book_id est l'ID du livre."""
        try:
            book = Book.objects.get(id=book_id)
            if book.copies_available > 0:
                Reservation.objects.create(user=request.user, book=book)
                return f"Succès : Le livre '{book.title}' a été réservé pour vous."
            return f"Erreur : Le livre '{book.title}' n'a plus d'exemplaires physiques disponibles."
        except Exception as e:
            return f"Erreur lors de la réservation : {str(e)}"

    def search_books_semantic(query: str):
        """Recherche des livres par sens (sémantique) et pas seulement par mots-clés."""
        try:
            # 1. Générer l'embedding de la requête
            model_emb = "models/gemini-embedding-001"
            result = genai.embed_content(model=model_emb, content=query, task_type="retrieval_query")
            query_embedding = result['embedding']
            
            # 2. Comparer avec les livres (Similarity Search basique)
            books = Book.objects.exclude(embedding__isnull=True)
            results = []
            for book in books:
                # Cosine Similarity simplifiée
                try:
                    dot_product = np.dot(query_embedding, book.embedding)
                    norm_q = np.linalg.norm(query_embedding)
                    norm_b = np.linalg.norm(book.embedding)
                    score = dot_product / (norm_q * norm_b)
                    results.append((book, score))
                except: continue
            
            results.sort(key=lambda x: x[1], reverse=True)
            top_books = results[:3]
            
            if not top_books: return "Aucun livre trouvé sémantiquement pour cette requête."
            
            # Format enrichi pour les cartes HTML dans le chat
            formatted_results = []
            for b, score in top_books:
                cover_url = b.cover_image.url if b.cover_image else "/static/img/default_book.jpg"
                formatted_results.append(f"BOOK_DATA: {b.title} | {b.author} | {b.id} | {cover_url} | {b.description[:100]}...")
            
            return "\n".join(formatted_results)
        except Exception as e:
            return f"Erreur technique lors de la recherche sémantique."

    def get_user_status():
        """Récupère l'état actuel de l'utilisateur (réservations, emprunts, retards)."""
        res = Reservation.objects.filter(user=request.user).exclude(status__in=['returned', 'cancelled'])
        if not res.exists(): return "L'utilisateur n'a aucune réservation ou emprunt en cours."
        return "Activités en cours : " + ", ".join([f"{r.book.title} (Statut: {r.get_status_display()})" for r in res])

    def update_interests(interests_list: list):
        """Met à jour les centres d'intérêt de l'utilisateur. interests_list est une liste de chaînes."""
        pref, _ = UserPreference.objects.get_or_create(user=request.user)
        # Fusionner sans doublons
        current = set(pref.interests)
        current.update(interests_list)
        pref.interests = list(current)
        pref.save()
        return f"Centres d'intérêt mis à jour : {', '.join(pref.interests)}"

    def get_library_overview():
        """Donne un aperçu global : nombre de livres et catégories disponibles."""
        from books.models import Book, Category
        cats = [c.name for c in Category.objects.all()]
        count = Book.objects.count()
        return f"La bibliothèque contient {count} ouvrages répartis dans les catégories suivantes : {', '.join(cats)}."

    def activate_coach_mode(book_id: int):
        """Active le mode coach pour un livre spécifique. L'IA devient un tuteur sur ce livre."""
        from books.models import Book
        from .models import ChatSession
        try:
            book = Book.objects.get(id=book_id)
            session = ChatSession.objects.get(user=request.user, is_active=True)
            session.is_coaching_mode = True
            session.current_book_context = book
            session.save()
            return f"Mode Coach ACTIVÉ pour le livre '{book.title}'. Je suis maintenant votre tuteur sur cet ouvrage."
        except Exception as e:
            return f"Erreur lors de l'activation du mode coach : {str(e)}"

    def deactivate_coach_mode():
        """Désactive le mode coach et revient au mode assistant normal."""
        from .models import ChatSession
        try:
            session = ChatSession.objects.get(user=request.user, is_active=True)
            session.is_coaching_mode = False
            session.current_book_context = None
            session.save()
            return "Mode Coach DÉSACTIVÉ. Je redeviens votre assistant bibliothèque normal."
        except Exception as e:
            return f"Erreur lors de la désactivation : {str(e)}"

    def generate_quiz(book_id: int):
        """Génère une question de quiz basée sur le contenu du livre pour tester l'étudiant."""
        from books.models import Book
        try:
            book = Book.objects.get(id=book_id)
            if not book.extracted_text:
                return "Je n'ai pas assez de contenu textuel sur ce livre pour générer un quiz précis. Posez-moi plutôt une question générale !"
            
            # On demande à l'IA (via le prompt système) de générer une question
            return f"ACTION_QUIZ: Génère maintenant une question à choix multiples basée sur le livre '{book.title}'."
        except:
            return "Désolé, je ne peux pas générer de quiz pour le moment."

    def add_cultural_points(points: int, reason: str):
        """Ajoute des points au score culturel de l'utilisateur pour sa participation (ex: quiz réussi)."""
        # Note: Dans notre modèle, le score est calculé dynamiquement, 
        # on peut créer une notification ou un log pour marquer l'effort
        from .models import Notification
        Notification.objects.create(
            recipient=request.user,
            notification_type='info',
            title="Points de culture !",
            message=f"Félicitations ! +{points} points ajoutés à votre profil pour : {reason}."
        )
        return f"Bravo ! Vous avez gagné {points} points de score culturel."

    return {
        "reserve_book": reserve_book,
        "search_books_semantic": search_books_semantic,
        "get_user_status": get_user_status,
        "update_interests": update_interests,
        "get_library_overview": get_library_overview,
        "activate_coach_mode": activate_coach_mode,
        "deactivate_coach_mode": deactivate_coach_mode,
        "generate_quiz": generate_quiz,
        "add_cultural_points": add_cultural_points
    }

@login_required
def chat_response(request):
    """
    Gère les réponses du chatbot SUPER-INTELLIGENT avec Tool Use, RAG et Mémoire.
    """
    from books.models import Book, Category
    from .models import ChatSession, ChatMessage, UserPreference
    from django.core.cache import cache
    import json
    
    user_message = request.POST.get('message', '')
    if not user_message: return HttpResponse("Message vide.")
    
    # 1. Gestion de la session et historique
    chat_session, created = ChatSession.objects.get_or_create(user=request.user, is_active=True)
    db_history = ChatMessage.objects.filter(session=chat_session).order_by('-created_at')[:10]
    db_history = reversed(list(db_history)) # Remettre dans l'ordre chronologique
    
    formatted_history = []
    for m in db_history:
        formatted_history.append({
            "role": "user" if m.role == 'user' else "model",
            "parts": [m.content]
        })
    
    # 2. Mémoire à Long Terme (Préférences)
    prefs, _ = UserPreference.objects.get_or_create(user=request.user)
    interests_ctx = ", ".join(prefs.interests) if prefs.interests else "Aucun détecté encore."

    # 3. Stats Globales
    stats = cache.get('library_chatbot_stats')
    if not stats:
        stats = {
            "total": Book.objects.count(),
            "categories": [c.name for c in Category.objects.all()[:5]]
        }
        cache.set('library_chatbot_stats', stats, 900)

    # 4. Préparation Gemini avec TOOLS
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key: return HttpResponse("Service indisponible.")

    # 4.5 Logique spécifique au Mode Coach
    coaching_context = ""
    if chat_session.is_coaching_mode and chat_session.current_book_context:
        book = chat_session.current_book_context
        # On récupère un extrait du livre (on limite pour les quotas)
        if book.extracted_text:
            # Recherche simple de mots clés pour extraire le passage le plus pertinent
            keywords = [w for w in user_message.lower().split() if len(w) > 3]
            content = book.extracted_text
            best_passage = content[:2000] # Fallback
            
            for kw in keywords:
                idx = content.lower().find(kw)
                if idx != -1:
                    start = max(0, idx - 500)
                    end = min(len(content), idx + 1500)
                    best_passage = content[start:end]
                    break
            
            coaching_context = f"\nTU ES EN MODE COACH pour le livre : '{book.title}'.\nCONTENU EXTRAIT DU LIVRE :\n{best_passage}\n"
        else:
            coaching_context = f"\nTU ES EN MODE COACH pour le livre : '{book.title}'.\nNOTE : Ce livre n'a pas de PDF, utilise tes connaissances générales sur ce titre/auteur ({book.author}) pour aider l'étudiant.\n"

    def stream_generator():
        # Liste des modèles par ordre de préférence pour le fallback
        models_to_try = [
            'models/gemini-1.5-flash-latest',
            'models/gemini-flash-latest',
            'models/gemini-2.0-flash',
            'models/gemini-2.5-flash-lite'
        ]
        
        last_error = ""
        for model_name in models_to_try:
            try:
                genai.configure(api_key=api_key)
                tools = get_chatbot_tools(request)
                
                system_prompt = f"""
                Tu es l'Expert Estim Library Premium. Ton but est d'être un assistant ultra-visuel et un coach pédagogique.
                {coaching_context}
                
                IDENTITÉ & STYLE :
                - Tu es pro-actif. N'attends pas les ordres.
                - Si l'utilisateur cherche un livre, utilise `search_books_semantic` et présente les résultats avec des balises HTML personnalisées.
                - Si le MODE COACH est activé : Utilise l'icône 🎓 et sois très tuteur.
                
                RÈGLES DE FORMATAGE (IMPORTANT) :
                1. CARTES DE LIVRES : Pour chaque livre trouvé, génère ce code HTML exact :
                   <div class="chat-book-card bg-surface-container-low border border-outline-variant/30 rounded-2xl p-3 my-2 flex gap-3">
                     <img src="URL_COUVERTURE" class="w-12 h-16 rounded-md object-cover shadow-sm">
                     <div class="flex-grow">
                        <p class="text-[11px] font-extrabold line-clamp-1">TITRE</p>
                        <p class="text-[9px] text-outline italic">AUTEUR</p>
                        <button onclick="reserveBook(ID)" class="mt-2 bg-primary text-white text-[8px] font-black px-3 py-1 rounded-full uppercase">Réserver</button>
                     </div>
                   </div>
                
                2. BOUTONS D'ACTION (CHIPS) : À la fin de tes messages, propose 2-3 boutons :
                   <div class="flex gap-2 mt-2">
                     <button onclick="sendQuickMsg('Quiz')" class="chip bg-secondary/10 text-secondary text-[9px] font-bold px-3 py-1.5 rounded-full border border-secondary/20">🎓 Mode Quiz</button>
                     <button onclick="sendQuickMsg('Résumé')" class="chip bg-primary/10 text-primary text-[9px] font-bold px-3 py-1.5 rounded-full border border-primary/20">📝 Résumé</button>
                   </div>

                CAPACITÉS (Outils) : 
                - `generate_quiz(book_id)` : Pour lancer un test.
                - `add_cultural_points(points, reason)` : Récompense l'utilisateur (ex: +10 pts pour un quiz réussi).
                - `activate_coach_mode(book_id)`, `reserve_book(book_id)`, `search_books_semantic(query)`.
                
                RÈGLES D'OR :
                - Ne dis pas "Bonjour" inutilement.
                - Si l'utilisateur répond juste à un quiz, appelle `add_cultural_points(10, "Quiz réussi")`.
                """

                model = genai.GenerativeModel(
                    model_name=model_name, 
                    system_instruction=system_prompt,
                    tools=list(tools.values())
                )
                
                safety_settings = [
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                ]
                
                chat = model.start_chat(history=formatted_history, enable_automatic_function_calling=True)
                response = chat.send_message(user_message, stream=False, safety_settings=safety_settings)
                
                if response.candidates and response.candidates[0].content.parts:
                    full_reply = response.text
                else:
                    full_reply = "Je n'ai pas pu formuler de réponse précise. Pouvez-vous reformuler ?"
                
                yield full_reply
                
                # Sauvegarde finale en base
                ChatMessage.objects.create(session=chat_session, role='user', content=user_message)
                ChatMessage.objects.create(session=chat_session, role='assistant', content=full_reply)
                return # Succès, on sort de la boucle de fallback

            except Exception as e:
                last_error = str(e)
                if "429" in last_error or "404" in last_error:
                    print(f"Fallback : Le modèle {model_name} a échoué ({last_error}), essai du suivant...")
                    continue 
                else:
                    print(f"Erreur critique ({model_name}): {last_error}")
                    break 

        # Si on arrive ici, tous les modèles ont échoué ou erreur critique
        if "429" in last_error:
            yield "Je reçois beaucoup de messages en ce moment ! Pouvez-vous patienter une petite minute avant de me relancer ? 😊"
        else:
            yield "Oups ! Je rencontre une petite difficulté technique pour vous répondre. Réessayez dans un instant ?"


    return StreamingHttpResponse(stream_generator(), content_type='text/plain')

@login_required
def get_chat_status(request):
    """Renvoie le statut actuel du chatbot (Normal ou Coach)."""
    from .models import ChatSession
    try:
        session = ChatSession.objects.get(user=request.user, is_active=True)
        return HttpResponse(json.dumps({
            'is_coaching_mode': session.is_coaching_mode,
            'book_title': session.current_book_context.title if session.current_book_context else None
        }), content_type='application/json')
    except:
        return HttpResponse(json.dumps({'is_coaching_mode': False}), content_type='application/json')

@login_required
def get_unread_notification_count(request):
    """Renvoie juste le nombre de notifications non lues pour HTMX."""
    count = request.user.notifications.filter(is_read=False).count()
    if count > 0:
        return HttpResponse(f'<span class="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-error text-[10px] font-bold text-white ring-2 ring-white animate-pulse">{count}</span>')
    return HttpResponse("")
