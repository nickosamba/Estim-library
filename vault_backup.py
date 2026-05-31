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
