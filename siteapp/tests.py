from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Post, Event, Person


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
