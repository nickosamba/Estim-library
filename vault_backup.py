import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

def create_backup():
    # 1. Configuration des dossiers
    BASE_DIR = Path(__file__).resolve().parent
    BACKUP_ROOT = BASE_DIR / "backups"
    TIMESTAMP = datetime.now().strftime("%Y_%m_%d_%Hh%M")
    CURRENT_BACKUP_DIR = BACKUP_ROOT / f"backup_{TIMESTAMP}"
    
    print(f"🚀 Démarrage de la sauvegarde complète : {TIMESTAMP}")
    
    # Création du dossier de sauvegarde
    if not os.path.exists(CURRENT_BACKUP_DIR):
        os.makedirs(CURRENT_BACKUP_DIR)
        print(f"✅ Dossier créé : {CURRENT_BACKUP_DIR}")

    # 2. Sauvegarde de la base de données SQLite (Fichier physique)
    db_path = BASE_DIR / "db.sqlite3"
    if db_path.exists():
        shutil.copy2(db_path, CURRENT_BACKUP_DIR / "db.sqlite3")
        print("✅ Base de données SQLite (physique) sauvegardée.")
    else:
        print("⚠️ Attention : db.sqlite3 introuvable dans le dossier racine.")

    # 3. Exportation des données Django (Format JSON pour la portabilité)
    json_dump_path = CURRENT_BACKUP_DIR / "full_data_export.json"
    print("⏳ Génération de l'export JSON (dumpdata)...")
    try:
        # Optimisation pour Alwaysdata : on exclut les tables lourdes (sessions, logs, historique chat)
        # et on retire l'indentation pour économiser de la RAM
        cmd = [
            'python', 'manage.py', 'dumpdata', 
            '--exclude', 'contenttypes', 
            '--exclude', 'auth.Permission', 
            '--exclude', 'sessions',
            '--exclude', 'admin.logentry',
            '--exclude', 'accounts.ChatMessage',  # Historique chat potentiellement lourd
            '--format', 'json'
        ]
        
        result = subprocess.run(cmd, capture_output=True, shell=False)
        
        if result.returncode == 0:
            with open(json_dump_path, 'wb') as f:
                f.write(result.stdout)
            print("✅ Export JSON terminé avec succès.")
        else:
            print(f"❌ Échec dumpdata (Code {result.returncode}).")
            # Fallback : on continue sans le JSON car le .sqlite3 est déjà là
    except Exception as e:
        print(f"⚠️ Note : L'export JSON a été ignoré ({e}). La sauvegarde physique .sqlite3 reste valide.")

    # 4. Sauvegarde des fichiers MÉDIAS (PDF et Images)
    media_dir = BASE_DIR / "media"
    if media_dir.exists():
        print("⏳ Sauvegarde des fichiers médias (PDF et images)...")
        shutil.copytree(media_dir, CURRENT_BACKUP_DIR / "media", dirs_exist_ok=True)
        print(f"✅ Dossier /media/ sauvegardé ({sum(f.stat().st_size for f in media_dir.glob('**/*') if f.is_file()) / (1024*1024):.2f} Mo).")
    else:
        print("⚠️ Dossier /media/ introuvable. Aucun fichier PDF ou image à sauvegarder.")

    print(f"\n✨ SAUVEGARDE TERMINÉE AVEC SUCCÈS !")
    print(f"📍 Emplacement : {CURRENT_BACKUP_DIR}")
    print("💡 Conseil : Copiez ce dossier sur une clé USB ou un Cloud pour une sécurité maximale.")

if __name__ == "__main__":
    create_backup()
