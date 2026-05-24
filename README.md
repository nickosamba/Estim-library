# 📚 Estim Library

**Estim Library** est une plateforme de gestion de bibliothèque moderne et immersive, conçue pour offrir une expérience de lecture exceptionnelle tout en simplifiant la gestion opérationnelle. Elle combine la gestion d'ouvrages physiques et numériques dans une interface élégante et performante.

---

## ✨ Fonctionnalités Clés

### 📖 Expérience de Lecture & Catalogue
- **Catalogue Hybride :** Gestion fluide des livres physiques (avec stock) et numériques (lecteur PDF intégré).
- **Auto-filtrage Intelligent :** Le catalogue s'adapte automatiquement au profil de l'utilisateur (Campus et Département).
- **Pagination Infinie :** Navigation ultra-fluide sans rechargement de page via HTMX.
- **Système de Recommandations :** Suggestions basées sur le cursus académique et les coups de cœur.

### 🛡️ Gestion & Administration
- **Dashboard de Pilotage :** Statistiques en temps réel sur le stock critique, les emprunts et les membres.
- **Gestion des Membres :** Annuaire complet avec recherche plein texte, filtrage par campus et détection automatique des retards.
- **Actions Groupées :** Mise en ligne/hors ligne et suppression massive d'ouvrages.
- **Notifications Sélectives :** Système d'alerte ciblé pour les bibliothécaires (réservations) et les étudiants (approbations).

### 📱 Technologie & Performance
- **PWA (Progressive Web App) :** Installable sur mobile avec support hors-ligne et raccourcis tactiles.
- **Optimisation SEO :** Sitemap dynamique, balises canoniques et données structurées (Schema.org) pour un référencement Google optimal.
- **Responsive Design :** Interface totalement optimisée pour smartphone, tablette et desktop.

---

## 🛠️ Stack Technique

- **Backend :** Django 5.2 (Python 3.10)
- **Frontend :** Tailwind CSS, Alpine.js, HTMX (pour une réactivité sans SPA)
- **Base de données :** SQLite (Développement/Petit déploiement) ou PostgreSQL
- **Fichiers Statiques :** WhiteNoise avec compression Manifest
- **Serveur Prod :** Gunicorn

---

## 🚀 Installation Locale

1. **Cloner le dépôt :**
   ```bash
   git clone https://github.com/votre-utilisateur/estimlib.git
   cd estimlib
   ```

2. **Créer un environnement virtuel :**
   ```bash
   python -m venv venv
   source venv/bin/scripts/activate  # Windows: venv\Scripts\activate
   ```

3. **Installer les dépendances :**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurer l'environnement :**
   - Copiez `.env.example` vers `.env`
   - Remplissez les variables (SECRET_KEY, EMAIL_HOST_USER, etc.)

5. **Lancer les migrations et le serveur :**
   ```bash
   python manage.py migrate
   python manage.py runserver 8099
   ```

---

## 🚢 Déploiement

Le projet inclut des scripts automatisés pour faciliter la mise en production :

- **Sur Linux/macOS :** 
  ```bash
  chmod +x deploy.sh
  ./deploy.sh
  ```
- **Sur Windows (PowerShell) :**
  ```powershell
  ./deploy.ps1
  ```

Ces scripts gèrent automatiquement l'installation, les migrations, la collecte des fichiers statiques, les vérifications de sécurité et les tests de santé.

---

## 📝 Licence

Ce projet est la propriété de **LABORATOIRE-AZ-TECH**. Tous droits réservés.
📧 Contact : aztech140@gmail.com

---
*Préserver l'héritage, inspirer le futur. — Estim Library 2026*
