#!/bin/bash

# Arrêter le script immédiatement en cas d'erreur
set -e

# Script de déploiement pour Estim Library (Linux/macOS)
echo "--- 🚀 Lancement du déploiement d'Estim Library ---"

# 0. Sauvegarde de sécurité automatique
echo "🔐 Sauvegarde de sécurité (Vault)..."
python vault_backup.py

# 1. Mise à jour des dépendances
echo "📦 Installation des dépendances..."
pip install -r requirements.txt

# 2. Migrations de la base de données
echo "🗄️ Migration de la base de données..."
python manage.py migrate --noinput

# 3. Collecte des fichiers statiques
echo "🎨 Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

# 4. Vérification de la configuration
echo "🛡️ Vérification de la sécurité..."
python manage.py check --deploy

# 5. Tests de santé
echo "🧪 Exécution des tests unitaires..."
python manage.py test

echo "--- ✅ Déploiement terminé avec succès ! ---"
echo "Vous pouvez maintenant lancer le serveur avec : gunicorn library_project.wsgi"
