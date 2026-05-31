from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

class Author(models.Model):
    name = models.CharField(max_length=200)
    biography = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Campus(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name_plural = "Campuses"

    def __str__(self):
        return self.name

class Book(models.Model):
    DEPARTMENT_CHOICES = (
        ('sciences', 'Sciences et Technologies'),
        ('management', 'Management et Gestion'),
        ('lettres', 'Lettres et Sciences Humaines'),
    )

    LEVEL_CHOICES = (
        ('L1', 'Licence 1'),
        ('L2', 'Licence 2'),
        ('L3', 'Licence 3'),
        ('M1', 'Master 1'),
        ('M2', 'Master 2'),
        ('DOC', 'Doctorat'),
    )

    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='books')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='books')
    
    # Academic targets
    target_campuses = models.ManyToManyField(Campus, blank=True, related_name='books')
    target_department = models.CharField(max_length=50, choices=DEPARTMENT_CHOICES, blank=True, null=True)
    target_level = models.CharField(max_length=10, choices=LEVEL_CHOICES, blank=True, null=True)
    target_filiere = models.CharField(max_length=100, blank=True, null=True, help_text="Option spécifique (ex: Informatique)")
    
    description = models.TextField()
    cover_image = models.ImageField(upload_to='books/covers/', blank=True, null=True)
    pdf_file = models.FileField(upload_to='books/pdfs/', blank=True, null=True)
    publication_year = models.PositiveIntegerField()
    isbn = models.CharField(max_length=13, unique=True, null=True, blank=True)
    copies_available = models.PositiveIntegerField(default=1)
    is_available = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False, verbose_name="Coup de cœur (Trésor du Mois)")
    
    # Advanced Intelligence Fields
    embedding = models.JSONField(null=True, blank=True, help_text="Représentation vectorielle pour la recherche sémantique")
    extracted_text = models.TextField(blank=True, help_text="Texte extrait du PDF pour analyse")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def is_available_at(self, campus):
        """
        Checks if the book is physically available at a given campus object.
        - If the book has no target campuses assigned, it's considered globally available.
        - If the book has target campuses, the user must belong to one of them or one must be 'all'.
        """
        if not self.target_campuses.exists():
            return True
        if not campus:
            return False
        return self.target_campuses.filter(models.Q(id=campus.id) | models.Q(code='all')).exists()

    def is_available_globally(self):
        """Checks if the book is available for all campuses."""
        return self.target_campuses.filter(code='all').exists()

    def update_ai_index(self):
        """Génère l'embedding et extrait le texte du PDF pour ce livre."""
        import google.generativeai as genai
        import os
        from PyPDF2 import PdfReader
        
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            return

        genai.configure(api_key=api_key)
        
        # 1. Extraction PDF
        if self.pdf_file:
            try:
                reader = PdfReader(self.pdf_file.path)
                text = ""
                for i in range(min(5, len(reader.pages))): # Limite à 5 pages pour l'automatisation
                    text += reader.pages[i].extract_text() + "\n"
                self.extracted_text = text
            except Exception as e:
                print(f"Erreur PDF ({self.title}): {e}")

        # 2. Embedding
        try:
            content = f"Titre: {self.title}\nDescription: {self.description}\nCatégorie: {self.category.name if self.category else ''}"
            result = genai.embed_content(
                model="models/gemini-embedding-001",
                content=content,
                task_type="retrieval_document"
            )
            self.embedding = result['embedding']
        except Exception as e:
            print(f"Erreur Embedding ({self.title}): {e}")
        
        # On utilise update() pour éviter de déclencher save() en boucle si appelé depuis un signal
        Book.objects.filter(id=self.id).update(
            embedding=self.embedding, 
            extracted_text=self.extracted_text
        )

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    @property
    def average_rating(self):
        avg = self.reviews.aggregate(models.Avg('rating'))['rating__avg']
        return round(avg, 1) if avg else 0
    
    @property
    def review_count(self):
        return self.reviews.count()

class Favorite(models.Model):
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='favorites')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='favorited_by')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'book')

    def __str__(self):
        return f"{self.user.username} - {self.book.title}"

class ReadingProgress(models.Model):
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='reading_progress')
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    last_page = models.PositiveIntegerField(default=1)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'book')

    def __str__(self):
        return f"{self.user.username} - {self.book.title} (Page {self.last_page})"

class Bookmark(models.Model):
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='bookmarks')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='bookmarks')
    page_number = models.PositiveIntegerField()
    label = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['page_number']

class Annotation(models.Model):
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='annotations')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='annotations')
    page_number = models.PositiveIntegerField()
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['page_number', '-created_at']

class Chapter(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='chapters')
    title = models.CharField(max_length=255)
    page_number = models.PositiveIntegerField()
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'page_number']

    def __str__(self):
        return f"{self.book.title} - {self.title} (p.{self.page_number})"

class Review(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('book', 'user')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.book.title} - {self.rating}"
