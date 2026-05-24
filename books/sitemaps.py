from django.contrib.sitemaps import Sitemap
from .models import Book

class BookSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Book.objects.filter(is_available=True)

    def lastmod(self, obj):
        return obj.created_at # Ou use updated_at si vous avez ce champ
