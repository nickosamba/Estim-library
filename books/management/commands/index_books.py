import os
import django
import sys
from pathlib import Path

# Setup Django
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_project.settings')
django.setup()

from django.core.management.base import BaseCommand
from books.models import Book
import google.generativeai as genai
from PyPDF2 import PdfReader
from dotenv import load_dotenv

load_dotenv(BASE_DIR / '.env')

class Command(BaseCommand):
    help = 'Génère les embeddings et extrait le texte des PDF pour tous les livres.'

    def handle(self, *args, **options):
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            self.stderr.write('GOOGLE_API_KEY non trouvée.')
            return

        genai.configure(api_key=api_key)
        books = Book.objects.all()

        for book in books:
            self.stdout.write(f"Traitement de : {book.title}")
            
            # 1. Extraction de texte si PDF présent
            if book.pdf_file and not book.extracted_text:
                try:
                    with book.pdf_file.open('rb') as f:
                        reader = PdfReader(f)
                        text = ""
                        # On limite à 10 pages pour ne pas exploser le contexte
                        max_pages = min(10, len(reader.pages))
                        for i in range(max_pages):
                            text += reader.pages[i].extract_text() + "\n"
                        book.extracted_text = text
                        self.stdout.write(f"  - Texte extrait ({len(text)} caractères)")
                except Exception as e:
                    self.stderr.write(f"  - Erreur extraction PDF: {e}")

            # 2. Génération d'embedding (Titre + Description)
            if not book.embedding:
                try:
                    content = f"Titre: {book.title}\nDescription: {book.description}\nCatégorie: {book.category.name if book.category else ''}"
                    result = genai.embed_content(
                        model="models/gemini-embedding-001",
                        content=content,
                        task_type="retrieval_document"
                    )
                    book.embedding = result['embedding']
                    self.stdout.write(f"  - Embedding généré")
                except Exception as e:
                    self.stderr.write(f"  - Erreur embedding: {e}")

            book.save()

        self.stdout.write(self.style.SUCCESS('Indexation terminée !'))

if __name__ == "__main__":
    Command().handle()
