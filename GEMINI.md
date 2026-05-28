# Instructions du Projet : Estim Library

## Règles de Développement Fondamentales

### 1. Protection du Module d'Inscription
- **STATUT** : VALIDÉ ET FIGÉ.
- **RÈGLE** : Ne jamais modifier les fichiers liés à l'inscription (`accounts/models.py`, `accounts/forms.py`, `register.html`) sans une directive explicite de l'utilisateur.
- **DÉTAILS** : Voir le fichier `REGISTRATION_VALIDATED.md` pour les spécifications techniques à maintenir.

### 2. Protection du Module de Connexion
- **STATUT** : VALIDÉ ET FIGÉ.
- **RÈGLE** : Ne pas modifier la logique d'authentification hybride (Email/Username), le système "Se souvenir de moi" et la configuration SMTP.
- **FICHIERS CLÉS** : 
    - `accounts/backends.py` (Logique Email/Username)
    - `accounts/forms.py` (EmailAuthenticationForm)
    - `accounts/views.py` (CustomLoginView)
    - `accounts/templates/accounts/login.html`
    - `accounts/templates/accounts/password_reset*` (Flux de réinitialisation)

### 3. Gestion des Utilisateurs
- Seul le **Superuser** (`is_superuser=True`) peut accéder à l'interface Django Admin (`/admin/`).
- Le champ `is_staff` est automatiquement géré par la méthode `save()` du modèle `User`.

### 4. Page d'Accueil & Recommandations
- **Système de Recommandations** : Doit filtrer les livres par Campus et Département de l'utilisateur s'il est connecté. Fallback sur une sélection aléatoire pour les anonymes.
- **Trésor du Mois** : Suit une hiérarchie stricte : 
    1. Livres marqués `is_featured=True`.
    2. Livres les mieux notés (>= 4 étoiles).
    3. Aléatoire parmi les livres avec image de couverture.
- **Statistiques** : Les compteurs de livres et membres doivent refléter l'état réel de la base de données.

### 5. Internationalisation
- Le projet doit rester en **Français** (`LANGUAGE_CODE = 'fr-fr'`).

### 6. Catalogue & Navigation
- **STATUT** : VALIDÉ ET FIGÉ.
- **Auto-filtrage Intelligent Inclusif** : Au premier chargement, le catalogue filtre par le Campus et le Département de l'étudiant, tout en incluant **systématiquement** les ouvrages "Tout Public" (ceux sans campus ou département assigné). Cela garantit que les ressources générales (dictionnaires, culture) sont toujours visibles.
- **Interface Simplifiée & Unique** : La liste des filtres exclut les campus virtuels (ex: "Tous les campus") pour ne montrer que les sites physiques. Le bouton "Tous les sites" sert de point d'entrée unique pour voir l'intégralité du fonds documentaire.
- **Protection contre les Doublons** : Utilisation systématique de `distinct()` sur les requêtes de filtrage pour éviter toute répétition d'ouvrages liée aux relations multi-campus.
- **Pagination Infinite Scroll** : Implémentation via HTMX (`hx-trigger="revealed"`) par lots de 12 ouvrages pour garantir la fluidité, quel que soit le volume de données.
- **Réservation HTMX Fluide** : Les réservations depuis le catalogue s'effectuent sans rechargement de page. Le bouton se transforme dynamiquement en badge d'état ("Réservé", "Déjà réservé", "Campus différent") pour une expérience utilisateur sans interruption.

### 7. Page Détail & Expérience Immersive
- **STATUT** : VALIDÉ ET FIGÉ.
- **Réservation HTMX Directe** : Intégration du flux HTMX sur la page détail pour une réservation instantanée sans rechargement, alignée sur le catalogue.
- **Recommandations Contextuelles** : Affichage dynamique d'ouvrages similaires basés sur la catégorie pour favoriser la découverte.
- **Suivi de Progression Intelligent** : Le bouton de lecture s'adapte automatiquement ("Lire" ou "Reprendre") avec affichage de la dernière page consultée pour les ouvrages PDF.
- **Partage Social Natif** : Utilisation de l'API Web Share pour un partage fluide sur mobile et fallback par copie de lien sur ordinateur.
- **Réactivité Mobile Premium** : Structure flexible (grilles adaptatives, barre d'action flottante) garantissant une ergonomie optimale sur tous les supports.

### 8. Gestion des Réservations Étudiants
- **STATUT** : VALIDÉ ET FIGÉ.
- **Organisation par État** : Séparation visuelle stricte entre les réservations actives (En cours) et l'historique (Terminé/Annulé).
- **Interaction HTMX** : L'annulation d'une réservation est instantanée via HTMX sans rechargement de page.
- **Alertes de Retard Critiques** : Détection automatique des retards avec badge "Retard Critique" clignotant et mise en évidence visuelle rouge.
- **Suivi de Lecture Unifié** : Affichage de la progression (Page X) directement sur la carte de réservation avec bouton intelligent ("Lire" ou "Reprendre").
- **Localisation & Guidage** : Rappel explicite du campus de retrait (pour les réservations approuvées) et du campus de retour (pour les emprunts en cours).
- **Transparence des Refus** : Affichage du motif de rejet fourni par le bibliothécaire dans l'historique pour une meilleure compréhension de l'étudiant.
- **Optimisation des États Vides** : Ajout de visuels et d'appels à l'action (CTA) vers le catalogue pour guider l'utilisateur si aucune donnée n'est disponible.

### 9. Centre de Notifications & Temps Réel
- **STATUT** : VALIDÉ ET FIGÉ.
- **Gestion Instantanée HTMX** : Les actions "Marquer comme lu", "Supprimer" et "Vider tout" s'effectuent sans rechargement de page pour une fluidité maximale.
- **Synchronisation du Compteur** : Le badge de notification dans la barre de navigation se met à jour dynamiquement via un événement HTMX (`updateNotificationCount`) dès qu'une action est effectuée.
- **Redirection Intelligente** : Les liens "Détails de l'activité" pointent dynamiquement vers le contexte pertinent (ex: Mes Réservations pour un étudiant, Dashboard pour le staff).
- **Interface Visuelle Adaptative** : Utilisation d'icônes spécifiques par type d'alerte (prêt, rendu, refus) et opacité réduite pour les notifications déjà lues.
- **Réactivité Mobile** : Affichage optimisé pour smartphone avec empilement vertical des éléments et transitions fluides lors des suppressions.

### 10. Profil Utilisateur & Gamification
- **STATUT** : VALIDÉ ET FIGÉ.
- **Statistiques Dynamiques Réelles** : Calcul automatique du nombre d'emprunts restitués et affichage du **Score Culturel** (basé sur l'activité de lecture et les avis postés).
- **Tableau de Bord d'Activité** : Les activités récentes intègrent des badges de progression de lecture ("P. X") sur les couvertures pour une continuité de lecture immédiate.
- **Formulaire de Modification Premium** : Interface de mise à jour stylisée avec des widgets personnalisés (listes déroulantes corrigées, styling Gold & Green, focus fluide) dans une fenêtre modale optimisée pour le scroll mobile.
- **Espace Gestionnaire Augmenté** : Affichage en temps réel des statistiques critiques (demandes en attente, nombre total de membres) pour les administrateurs et le staff.
- **Expérience Visuelle** : Utilisation de motifs africains en overlay et de transitions fluides pour un rendu immersif et professionnel.

### 11. Dashboard Administrateur & Staff
- **STATUT** : VALIDÉ ET FIGÉ.
- **Pilotage Analytique (Admin)** : Widgets de performance en temps réel (Disponibilité, Stock critique, Diversité) et graphiques analytiques par département/niveau.
- **Gestion Opérationnelle HTMX (Staff)** : Mise à jour des statuts de réservation sans rechargement de page, avec synchronisation dynamique des compteurs de statistiques.
- **Formulaire d'Ajout Rapide & Ergonome** : 
    - Le formulaire de création d'ouvrage intègre des boutons d'**Ajout Rapide** pour les **Auteurs** et les **Catégories**, permettant de créer ces entités à la volée sans quitter le formulaire.
    - Le champ **Description / Résumé** est strictement **obligatoire** pour garantir la qualité du catalogue et l'efficacité de la recherche plein texte.
- **Actions Groupées (Catalogue)** : Interface de modification en masse (En ligne, Hors ligne, Suppression) pour une gestion efficace du stock.
- **Gestion Hybride (Physique/Numérique)** : 
    - Les ouvrages disposant d'une version PDF et ayant 0 exemplaire physique ne sont plus comptabilisés dans le **Stock Critique**.
    - Dans le Dashboard, ces ouvrages affichent un indicateur visuel "Edition PDF" et leur stock ne clignote plus en rouge.
- **Réactivité Mobile Premium** : Transformation automatique du tableau en cartes interactives sur smartphone pour une gestion fluide "sur le terrain".
- **Redirection Intelligente** : Les rôles de gestion sont automatiquement redirigés vers le Dashboard dès la connexion.

### 12. Logique d'Affichage Intelligente (Numérique)
- **STATUT** : VALIDÉ ET FIGÉ.
- **Bouton d'Action Dynamique** : Dans le catalogue et la fiche détail, si un livre a un stock physique nul mais possède un PDF, le bouton "Réserver" est automatiquement remplacé par **"Lire l'ouvrage"** (ou "Accès Numérique").
- **Badges de Statut Précis** : Utilisation du badge "**Édition Numérique**" (Bleu/Gold) au lieu de "Disponible" pour les ouvrages purement numériques, évitant la confusion avec le stock physique "En rayon".
- **Alertes de Stock Cohérentes** : Les alertes de stock critique (clignotement rouge) sont réservées exclusivement aux ouvrages physiques en pénurie.

### 13. Gestion des Membres & Pilotage
- **STATUT** : VALIDÉ ET FIGÉ.
- **Recherche & Filtrage HTMX** : La liste des membres intègre une recherche plein texte et des filtres par **Campus** et **Département** avec mise à jour instantanée sans rechargement.
- **Surveillance des Retards** : Détection automatique des emprunts expirés avec affichage d'un badge "**Retard**" clignotant et d'une icône d'alerte sur le profil du membre.
- **Pagination Infinie** : Chargement par lots de 20 membres pour garantir la performance sur les gros volumes d'utilisateurs.
- **Responsive Design Avancé** : Le tableau des membres s'adapte dynamiquement sur mobile en fusionnant les informations (Auteur/Cursus sous le nom) et en masquant les colonnes secondaires.
- **Distribution Sélective des Alertes** : Les notifications de **Nouvelles Réservations** sont envoyées exclusivement aux utilisateurs ayant le rôle **Bibliothécaire** (`role='librarian'`). L'Administrateur est déchargé de ce flux opérationnel tout en gardant l'accès aux statistiques globales.
