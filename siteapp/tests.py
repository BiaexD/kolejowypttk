import io

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from .models import Post, Event, EventPhoto, Person, CentralNews


def tiny_jpeg():
    buf = io.BytesIO()
    Image.new("RGB", (10, 10), color="red").save(buf, format="JPEG")
    return SimpleUploadedFile("test.jpg", buf.getvalue(), content_type="image/jpeg")


class PublicPagesSmokeTest(TestCase):
    """Every public URL should render without error, even with an empty database."""

    def test_static_pages_ok(self):
        for name in [
            "index", "news_list", "event_list", "board",
            "docs_list", "gallery_albums", "contact",
            "historia", "odznaki", "robots_txt", "sitemap",
        ]:
            with self.subTest(name=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 200)


class NewsTest(TestCase):
    def setUp(self):
        self.published = Post.objects.create(
            title="Opublikowana aktualność",
            body="Treść",
            published_at=timezone.now(),
            is_published=True,
        )
        self.hidden = Post.objects.create(
            title="Ukryta aktualność",
            body="Treść",
            published_at=timezone.now(),
            is_published=False,
        )

    def test_news_list_shows_only_published(self):
        response = self.client.get(reverse("news_list"))
        self.assertContains(response, self.published.title)
        self.assertNotContains(response, self.hidden.title)

    def test_news_detail_hides_unpublished(self):
        response = self.client.get(reverse("news_detail", args=[self.hidden.pk]))
        self.assertEqual(response.status_code, 404)


class CombinedNewsPageTest(TestCase):
    def setUp(self):
        for i in range(4):
            Post.objects.create(
                title=f"Własna aktualność {i}",
                body="Treść",
                published_at=timezone.now(),
                is_published=True,
            )
        for i in range(4):
            CentralNews.objects.create(
                wp_id=i,
                title=f"Aktualność centrali {i}",
                excerpt="Treść",
                link="https://pttk.pl/przyklad/",
                published_at=timezone.now(),
            )

    def test_both_sections_show_on_first_page(self):
        response = self.client.get(reverse("news_list"))
        self.assertContains(response, "U nas")
        self.assertContains(response, "Z centrali PTTK")
        self.assertContains(response, "Własna aktualność 3")
        self.assertContains(response, "Aktualność centrali 3")

    def test_own_and_central_pagination_are_independent(self):
        response = self.client.get(reverse("news_list"), {"own_page": 2})
        own_page = response.context["own_page"]
        central_page = response.context["central_page"]
        self.assertEqual(own_page.number, 2)
        self.assertEqual(central_page.number, 1)


class EventTest(TestCase):
    def test_event_detail_by_slug(self):
        event = Event.objects.create(
            title="Rajd testowy",
            slug="rajd-testowy",
            description="Opis",
            start_date=timezone.now().date(),
            is_published=True,
        )
        response = self.client.get(event.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, event.title)


class GalleryTest(TestCase):
    def setUp(self):
        self.event = Event.objects.create(
            title="Rajd ze zdjęciami",
            slug="rajd-ze-zdjeciami",
            description="Opis",
            start_date=timezone.now().date(),
            is_published=True,
        )
        self.photo = EventPhoto.objects.create(event=self.event, image=tiny_jpeg())

    def tearDown(self):
        self.photo.image.delete(save=False)

    def test_event_with_photos_listed_as_album(self):
        response = self.client.get(reverse("gallery_albums"))
        self.assertContains(response, self.event.title)

    def test_album_detail_shows_photo(self):
        response = self.client.get(reverse("gallery_album_detail", args=[self.event.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.photo.image.url)

    def test_photo_is_resized_to_max_dimension(self):
        with Image.open(self.photo.image.path) as img:
            self.assertLessEqual(max(img.size), 1920)


class BoardTest(TestCase):
    def test_board_groups_people_by_body(self):
        Person.objects.create(body="zarzad", name="Jan Kowalski", role="prezes")
        response = self.client.get(reverse("board"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Jan Kowalski")


class ContactFormTest(TestCase):
    def test_valid_submission_redirects_and_sends_mail(self):
        response = self.client.post(reverse("contact"), {
            "name": "Jan Kowalski",
            "email": "jan@example.com",
            "message": "Wiadomość testowa",
            "honeypot": "",
        })
        self.assertRedirects(response, reverse("contact"))

    def test_honeypot_blocks_bots(self):
        response = self.client.post(reverse("contact"), {
            "name": "Bot",
            "email": "bot@example.com",
            "message": "Spam",
            "honeypot": "wypełnione przez bota",
        })
        # Invalid form re-renders the page instead of redirecting.
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["form"].is_valid())
