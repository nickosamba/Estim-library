# Script de deploiement pour Estim Library (Windows PowerShell)
Write-Host "--- Lancement du deploiement ---" -ForegroundColor Cyan

# 0. Sauvegarde de securite automatique
Write-Host "Sauvegarde de securite (Vault)..." -ForegroundColor Magenta
python vault_backup.py

# 1. Mise a jour des dependances
Write-Host "Installation des dependances..." -ForegroundColor Yellow
python -m pip install -r requirements.txt

# 2. Migrations de la base de donnees
Write-Host "Migration de la base de donnees..." -ForegroundColor Yellow
python manage.py migrate --noinput

# 3. Collecte des fichiers statiques
Write-Host "Collecte des fichiers statiques..." -ForegroundColor Yellow
python manage.py collectstatic --noinput

# 4. Verification de la configuration
Write-Host "Verification de la securite..." -ForegroundColor Yellow
python manage.py check --deploy

# 5. Tests de sante
Write-Host "Execution des tests unitaires..." -ForegroundColor Yellow
python manage.py test

Write-Host "--- Deploiement termine avec succes ! ---" -ForegroundColor Green
Write-Host "Pret pour gunicorn library_project.wsgi"
