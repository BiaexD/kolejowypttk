from django.db import models
from django.urls import reverse


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


class Person(TimeStamped):
    ROLE_CHOICES = [
        ('prezes', 'Prezes'),
        ('wiceprezes', 'Wiceprezes'),
        ('sekretarz', 'Sekretarz'),
        ('skarbnik', 'Skarbnik'),
        ('czlonek', 'Członek zarządu'),
    ]
    name = models.CharField(max_length=120)
    role = models.CharField(max_length=40, choices=ROLE_CHOICES, db_index=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    photo_url = models.URLField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'role', 'name']
        verbose_name = 'Osoba'
        verbose_name_plural = 'Władze'

    def __str__(self):
        return f"{self.name} ({self.get_role_display()})"


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


class FbAlbum(TimeStamped):
    fb_album_id = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=200, blank=True)
    count = models.PositiveIntegerField(default=0)
    cover_photo_id = models.CharField(max_length=64, blank=True)

    class Meta:
        ordering = ['-updated']
        verbose_name = 'Album FB'
        verbose_name_plural = 'Albumy FB'

    def __str__(self):
        return self.name or self.fb_album_id

class FbPhoto(TimeStamped):
    fb_photo_id = models.CharField(max_length=64, unique=True)
    album = models.ForeignKey(FbAlbum, null=True, blank=True, on_delete=models.SET_NULL)
    created_time = models.DateTimeField(db_index=True)
    permalink_url = models.URLField()
    image_url = models.URLField()
    thumb_url = models.URLField(blank=True)
    caption = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_time']
        verbose_name = 'Zdjęcie FB'
        verbose_name_plural = 'Zdjęcia FB'

    def __str__(self):
        return self.caption or self.fb_photo_id


class HeroImage(TimeStamped):
    image_url = models.CharField()
    title = models.CharField(max_length=140, blank=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    class Meta:
        ordering = ['order', 'created']
        verbose_name = 'Slajd (hero)'
        verbose_name_plural = 'Slajdy (hero)'
    def __str__(self): return self.title or self.image_url