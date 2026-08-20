from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Post, Event


class StaticViewSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.5

    def items(self):
        return [
            "index", "news_list", "event_list", "board",
            "docs_list", "gallery_albums", "contact", "historia", "odznaki",
        ]

    def location(self, item):
        return reverse(item)


class NewsSitemap(Sitemap):
    changefreq = "never"
    priority = 0.6

    def items(self):
        return Post.objects.filter(is_published=True)

    def location(self, obj):
        return reverse("news_detail", args=[obj.pk])

    def lastmod(self, obj):
        return obj.updated


class EventSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        return Event.objects.filter(is_published=True)

    def lastmod(self, obj):
        return obj.updated
