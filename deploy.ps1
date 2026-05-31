# Script de deploiement pour Estim Library (Windows PowerShell)
Write-Host "--- Lancement du deploiement ---" -ForegroundColor Cyan

# 0. Sauvegarde de securite automatique
Write-Host "Sauvegarde de securite (Vault)..." -ForegroundColor Magenta
python vault_backup.py

# 1. Mise a jour des dependances
Write-Host "Installation des dependances..." -ForegroundColor Yellow
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# 2. Migrations de la base de donnees
Write-Host "Migration de la base de donnees..." -ForegroundColor Yellow
python manage.py migrate --noinput

# 3. Collecte et compression des fichiers statiques
Write-Host "Collecte et compression des fichiers statiques..." -ForegroundColor Yellow
python manage.py collectstatic --noinput

# 3.5 Vérification de la connexion au stockage Cloud R2 (si activé)
$envFile = Get-Content .env -ErrorAction SilentlyContinue
if ($envFile -like "*USE_R2=True*") {
    Write-Host "Stockage Cloud R2 detecte, verification de la configuration..." -ForegroundColor Magenta
    python manage.py check
}

# 4. Verification de la configuration
Write-Host "Verification de la securite..." -ForegroundColor Yellow
python manage.py check --deploy

# 4.5 Indexation IA (Nouveau)
Write-Host "Indexation sémantique des livres..." -ForegroundColor Yellow
python manage.py index_books

# 5. Tests de sante
Write-Host "Execution des tests unitaires..." -ForegroundColor Yellow
python manage.py test

Write-Host "--- Deploiement termine avec succes ! ---" -ForegroundColor Green
Write-Host "Pret pour gunicorn library_project.wsgi"
