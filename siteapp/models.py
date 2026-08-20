from django.db import models
from django.urls import reverse

from .imaging import resize_and_compress


class TimeStamped(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Post(TimeStamped):
    SOURCE_CHOICES = [
        ('MANUAL','Ręczny'),
        ('FACEBOOK','Facebook')
    ]
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES, default='MANUAL', db_index=True)
    title = models.CharField(max_length=200, blank=True)
    body = models.TextField(blank=True)
    image_url = models.URLField(blank=True)
    published_at = models.DateTimeField(db_index=True)
    is_published = models.BooleanField(default=True)

    fb_post_id = models.CharField(max_length=64, blank=True, null=True, unique=True)
    fb_perma   = models.URLField(blank=True)

    class Meta:
        ordering = ['-published_at']

    def __str__(self):
        return self.title or f"Post #{self.pk}"

    def first_image(self):
        first = self.images.order_by("order", "id").first()
        if first:
            return first.image.url
        return self.image_url


class PostImage(TimeStamped):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name="Aktualność",
    )
    image = models.ImageField(upload_to="news/")
    caption = models.CharField(max_length=255, blank=True, verbose_name="Podpis")
    order = models.PositiveIntegerField(default=0, verbose_name="Kolejność")

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Zdjęcie aktualności"
        verbose_name_plural = "Zdjęcia aktualności"

    def __str__(self):
        return f"Zdjęcie do: {self.post}"


class Event(TimeStamped):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    description = models.TextField()
    start_date = models.DateField(db_index=True)
    end_date = models.DateField(blank=True, null=True)
    location = models.CharField(max_length=200, blank=True)
    cover_url = models.URLField(blank=True)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ['start_date', 'title']
        verbose_name = 'Wydarzenie'
        verbose_name_plural = 'Wydarzenia'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('event_detail', args=[self.slug])

    def cover_photo(self):
        first = self.photos.order_by("order", "id").first()
        return first.image.url if first else self.cover_url


class EventPhoto(TimeStamped):
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="photos",
        verbose_name="Wydarzenie",
    )
    image = models.ImageField(upload_to="gallery/")
    caption = models.CharField(max_length=255, blank=True, verbose_name="Podpis")
    order = models.PositiveIntegerField(default=0, verbose_name="Kolejność")

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Zdjęcie z wydarzenia"
        verbose_name_plural = "Zdjęcia z wydarzeń"

    def __str__(self):
        return f"Zdjęcie: {self.event}"

    def save(self, *args, **kwargs):
        is_new_upload = bool(self.image) and not self.image._committed
        super().save(*args, **kwargs)
        if is_new_upload:
            resize_and_compress(self.image)
            EventPhoto.objects.filter(pk=self.pk).update(image=self.image.name)


class Person(TimeStamped):
    BODY_CHOICES = [
        ("zarzad", "Zarząd Oddziału"),
        ("sad", "Sąd Koleżeński Oddziału"),
        ("komisja", "Komisja Rewizyjna Oddziału"),
    ]

    ROLE_CHOICES = [
        # Zarząd (Twoje obecne)
        ("prezes", "Prezes"),
        ("wiceprezes", "Wiceprezes"),
        ("sekretarz", "Sekretarz"),
        ("skarbnik", "Skarbnik"),
        ("czlonek", "Członek"),

        # Uniwersalne dla sądu/komisji (i też mogą się przydać w zarządzie)
        ("przewodniczacy", "Przewodniczący"),
        ("zastepca", "Zastępca przewodniczącego"),
    ]

    body = models.CharField(
        max_length=20,
        choices=BODY_CHOICES,
        default="zarzad",
        db_index=True,
        verbose_name="Organ",
    )
    name = models.CharField(max_length=120, verbose_name="Imię i nazwisko")
    role = models.CharField(max_length=40, choices=ROLE_CHOICES, db_index=True, verbose_name="Funkcja")
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    photo_url = models.URLField(blank=True)
    order = models.PositiveIntegerField(default=0, help_text="Kolejność wyświetlania w ramach organu")

    class Meta:
        ordering = ["body", "order", "role", "name"]
        verbose_name = "Osoba"
        verbose_name_plural = "Władze"

    def __str__(self):
        return f"{self.name} ({self.get_role_display()} – {self.get_body_display()})"


class CentralNews(TimeStamped):
    """Aktualność zaimportowana z pttk.pl (centrala), przez WP REST API."""
    wp_id = models.PositiveIntegerField(unique=True)
    title = models.CharField(max_length=300)
    excerpt = models.TextField(blank=True)
    link = models.URLField()
    image_url = models.URLField(blank=True)
    published_at = models.DateTimeField(db_index=True)

    class Meta:
        ordering = ['-published_at']
        verbose_name = 'Aktualność z centrali PTTK'
        verbose_name_plural = 'Aktualności z centrali PTTK'

    def __str__(self):
        return self.title


class Document(TimeStamped):
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=120, blank=True)
    file_url = models.URLField()
    is_public = models.BooleanField(default=True)

    class Meta:
        ordering = ['category', 'title']
        verbose_name = 'Dokument'
        verbose_name_plural = 'Dokumenty'

    def __str__(self):
        return self.title


class HeroImage(TimeStamped):
    image_url = models.CharField(max_length=255, help_text="Ścieżka względna w static/, np. img/hero1.jpg")
    title = models.CharField(max_length=140, blank=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    class Meta:
        ordering = ['order', 'created']
        verbose_name = 'Slajd (hero)'
        verbose_name_plural = 'Slajdy (hero)'
    def __str__(self): return self.title or self.image_url