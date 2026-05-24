# Script de déploiement pour Estim Library (Windows PowerShell)
Write-Host "--- 🚀 Lancement du déploiement d'Estim Library ---" -ForegroundColor Cyan

# 1. Mise à jour des dépendances
Write-Host "📦 Installation des dépendances..." -ForegroundColor Yellow
python -m pip install -r requirements.txt

# 2. Migrations de la base de données
Write-Host "🗄️ Migration de la base de données..." -ForegroundColor Yellow
python manage.py migrate --noinput

# 3. Collecte des fichiers statiques
Write-Host "🎨 Collecte des fichiers statiques..." -ForegroundColor Yellow
python manage.py collectstatic --noinput

# 4. Vérification de la configuration
Write-Host "🛡️ Vérification de la sécurité..." -ForegroundColor Yellow
python manage.py check --deploy

# 5. Tests de santé
Write-Host "🧪 Exécution des tests unitaires..." -ForegroundColor Yellow
python manage.py test

Write-Host "--- ✅ Déploiement terminé avec succès ! ---" -ForegroundColor Green
Write-Host "Vous pouvez maintenant lancer le serveur avec : gunicorn library_project.wsgi"
