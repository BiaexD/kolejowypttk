from django.db import models
from django.urls import reverse
from django.utils import timezone

from .imaging import resize_and_compress


class TimeStamped(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class ActiveManager(models.Manager):
    """Domyślny menedżer — pomija to, co jest w koszu."""

    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class Trashable(models.Model):
    """Miękkie usuwanie: 'Usuń' w panelu przenosi do kosza, nie kasuje od razu."""

    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = ActiveManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=['is_deleted', 'deleted_at'])


class Post(TimeStamped, Trashable):
    SOURCE_CHOICES = [
        ('MANUAL','Ręczny'),
        ('FACEBOOK','Facebook')
    ]
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES, default='MANUAL', db_index=True)
    title = models.CharField(max_length=200, blank=True, verbose_name="Tytuł")
    body = models.TextField(blank=True, verbose_name="Treść")
    image_url = models.URLField(blank=True, verbose_name="Zdjęcie (stary URL, zaawansowane)")
    published_at = models.DateTimeField(db_index=True, verbose_name="Data publikacji")
    is_published = models.BooleanField(default=True, verbose_name="Opublikowana")

    fb_post_id = models.CharField(max_length=64, blank=True, null=True, unique=True)
    fb_perma   = models.URLField(blank=True, verbose_name="Link do posta na Facebooku")

    class Meta:
        ordering = ['-published_at']
        verbose_name = "Aktualność"
        verbose_name_plural = "Aktualności"

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
    image = models.ImageField(upload_to="news/", verbose_name="Zdjęcie")
    caption = models.CharField(max_length=255, blank=True, verbose_name="Podpis")
    order = models.PositiveIntegerField(default=0, verbose_name="Kolejność")

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Zdjęcie aktualności"
        verbose_name_plural = "Zdjęcia aktualności"

    def __str__(self):
        return f"Zdjęcie do: {self.post}"


class PostDocument(TimeStamped):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="documents",
        verbose_name="Aktualność",
    )
    file = models.FileField(upload_to="news_documents/", verbose_name="Plik")
    title = models.CharField(max_length=200, blank=True, verbose_name="Nazwa")

    class Meta:
        ordering = ["id"]
        verbose_name = "Dokument aktualności"
        verbose_name_plural = "Dokumenty aktualności"

    def __str__(self):
        return self.title or f"Dokument do: {self.post}"


class Event(TimeStamped, Trashable):
    title = models.CharField(max_length=200, verbose_name="Tytuł")
    slug = models.SlugField(max_length=220, unique=True, verbose_name="Slug (adres w URL)")
    description = models.TextField(verbose_name="Opis")
    start_date = models.DateField(db_index=True, verbose_name="Data rozpoczęcia")
    start_time = models.TimeField(blank=True, null=True, verbose_name="Godzina rozpoczęcia")
    end_date = models.DateField(blank=True, null=True, verbose_name="Data zakończenia")
    end_time = models.TimeField(blank=True, null=True, verbose_name="Godzina zakończenia")
    location = models.CharField(max_length=200, blank=True, verbose_name="Miejsce rozpoczęcia")
    location_lat = models.FloatField(null=True, blank=True, verbose_name="Miejsce — szerokość geogr.")
    location_lng = models.FloatField(null=True, blank=True, verbose_name="Miejsce — długość geogr.")
    end_location = models.CharField(max_length=200, blank=True, verbose_name="Miejsce zakończenia")
    end_location_lat = models.FloatField(null=True, blank=True, verbose_name="Miejsce zakończenia — szerokość geogr.")
    end_location_lng = models.FloatField(null=True, blank=True, verbose_name="Miejsce zakończenia — długość geogr.")
    cover_url = models.URLField(blank=True, verbose_name="Zdjęcie okładkowe (stary URL, zaawansowane)")
    is_published = models.BooleanField(default=True, verbose_name="Opublikowane")

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

    def map_link_url(self):
        if self.location_lat is None or self.location_lng is None:
            return None
        return (
            f"https://www.openstreetmap.org/?mlat={self.location_lat}&mlon={self.location_lng}"
            f"#map=16/{self.location_lat}/{self.location_lng}"
        )

    def end_map_link_url(self):
        if self.end_location_lat is None or self.end_location_lng is None:
            return None
        return (
            f"https://www.openstreetmap.org/?mlat={self.end_location_lat}&mlon={self.end_location_lng}"
            f"#map=16/{self.end_location_lat}/{self.end_location_lng}"
        )


class EventPhoto(TimeStamped):
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="photos",
        verbose_name="Wydarzenie",
    )
    image = models.ImageField(upload_to="gallery/", verbose_name="Zdjęcie")
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


class EventDocument(TimeStamped):
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="documents",
        verbose_name="Wydarzenie",
    )
    file = models.FileField(upload_to="event_documents/", verbose_name="Plik")
    title = models.CharField(max_length=200, blank=True, verbose_name="Nazwa")

    class Meta:
        ordering = ["id"]
        verbose_name = "Dokument wydarzenia"
        verbose_name_plural = "Dokumenty wydarzenia"

    def __str__(self):
        return self.title or f"Dokument do: {self.event}"


class Person(TimeStamped, Trashable):
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
    email = models.EmailField(blank=True, verbose_name="Email")
    phone = models.CharField(max_length=30, blank=True, verbose_name="Telefon")
    photo_url = models.URLField(blank=True, verbose_name="Zdjęcie (URL, nieużywane obecnie na stronie)")
    order = models.PositiveIntegerField(default=0, verbose_name="Kolejność", help_text="Kolejność wyświetlania w ramach organu")

    class Meta:
        ordering = ["body", "order", "role", "name"]
        verbose_name = "Osoba"
        verbose_name_plural = "Władze"

    def __str__(self):
        return f"{self.name} ({self.get_role_display()} – {self.get_body_display()})"


class CentralNews(TimeStamped):
    """Aktualność zaimportowana z zewnętrznej strony PTTK (WordPress) przez WP REST API."""

    SOURCE_CENTRALA = 'centrala'
    SOURCE_WKO = 'wko'
    SOURCE_CHOICES = [
        (SOURCE_CENTRALA, 'Centrala PTTK'),
        (SOURCE_WKO, 'Wielkopolska Korporacja Oddziałów PTTK'),
    ]

    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default=SOURCE_CENTRALA)
    wp_id = models.PositiveIntegerField()
    title = models.CharField(max_length=300)
    excerpt = models.TextField(blank=True)
    link = models.URLField()
    image_url = models.URLField(blank=True)
    published_at = models.DateTimeField(db_index=True)

    class Meta:
        ordering = ['-published_at']
        verbose_name = 'Aktualność zewnętrzna PTTK'
        verbose_name_plural = 'Aktualności zewnętrzne PTTK'
        constraints = [
            models.UniqueConstraint(fields=['source', 'wp_id'], name='uniq_centralnews_source_wp_id'),
        ]

    def __str__(self):
        return self.title


class Document(TimeStamped, Trashable):
    title = models.CharField(max_length=200, verbose_name="Tytuł")
    category = models.CharField(max_length=120, blank=True, verbose_name="Kategoria")
    file = models.FileField(upload_to="documents/", blank=True, verbose_name="Plik")
    file_url = models.URLField(
        blank=True,
        verbose_name="Link zewnętrzny (zaawansowane)",
        help_text="Użyj tylko, gdy dokument jest hostowany gdzie indziej. W innym wypadku wgraj plik powyżej.",
    )
    is_public = models.BooleanField(default=True, verbose_name="Widoczny publicznie")

    class Meta:
        ordering = ['category', 'title']
        verbose_name = 'Dokument'
        verbose_name_plural = 'Dokumenty'

    def __str__(self):
        return self.title

    def url(self):
        return self.file.url if self.file else self.file_url


class HeroImage(TimeStamped, Trashable):
    image = models.ImageField(upload_to="hero/", blank=True, verbose_name="Zdjęcie")
    image_url = models.CharField(
        max_length=255, blank=True,
        verbose_name="Ścieżka statyczna (zaawansowane)",
        help_text="Tylko dla starszych wpisów. Nowe zdjęcia wgrywaj przez pole „Zdjęcie” powyżej.",
    )
    title = models.CharField(max_length=140, blank=True, verbose_name="Tytuł (opcjonalnie)")
    is_active = models.BooleanField(default=True, verbose_name="Aktywny")
    order = models.PositiveIntegerField(default=0, verbose_name="Kolejność")

    class Meta:
        ordering = ['order', 'created']
        verbose_name = 'Slajd (hero)'
        verbose_name_plural = 'Slajdy (hero)'

    def __str__(self):
        return self.title or self.image_url or (self.image.name if self.image else "Slajd")

    def save(self, *args, **kwargs):
        is_new_upload = bool(self.image) and not self.image._committed
        super().save(*args, **kwargs)
        if is_new_upload:
            resize_and_compress(self.image)
            HeroImage.objects.filter(pk=self.pk).update(image=self.image.name)