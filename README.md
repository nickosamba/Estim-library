# Heritage Library - Estim Library

Une application Django moderne pour la gestion de bibliothèque, incluant une liseuse PDF premium, un système de réservations, et des outils d'import/export pour le staff.

## Fonctionnalités
- **Lecteurs** : Catalogue avec recherche HTMX, favoris, système d'avis, et liseuse PDF immersive (Mode Zen, Mode Sombre, Marque-pages, Annotations).
- **Staff** : Tableau de bord de statistiques, gestion des membres, import/export Excel/CSV, remplissage automatique des livres via ISBN (Google Books & Open Library).
- **Sécurité** : Gestion des rôles (Étudiant, Enseignant, Admin), protection des fichiers PDF.

## Installation

1. Cloner le dépôt :
   ```bash
   git clone <url-du-depot>
   cd library_project
   ```

2. Créer un environnement virtuel et l'activer :
   ```bash
   python -m venv env
   # Windows
   .\env\Scripts\activate
   # Linux/Mac
   source env/bin/activate
   ```

3. Installer les dépendances :
   ```bash
   pip install -r requirements.txt
   ```

4. Configurer les variables d'environnement :
   - Copier `.env.example` vers `.env`
   - Remplir la `SECRET_KEY` et ajuster les paramètres.

5. Appliquer les migrations et lancer le serveur :
   ```bash
   python manage.py migrate
   python manage.py runserver 8099
   ```

## Accès par défaut
- **Superuser** : `admin` / `adminpass123`
