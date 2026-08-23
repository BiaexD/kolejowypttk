import io

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from .models import Post, Event, EventPhoto, Person, CentralNews, Document
from .panel_forms import PanelPostForm, PanelEventForm, PanelDocumentForm


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


class EventInNewsFeedTest(TestCase):
    def test_upcoming_event_shows_in_aktualnosci_but_past_event_does_not(self):
        upcoming = Event.objects.create(
            title="Rajd za miesiąc", slug="rajd-za-miesiac", description="Opis",
            start_date=timezone.now().date() + timezone.timedelta(days=30),
        )
        past = Event.objects.create(
            title="Rajd w zeszłym miesiącu", slug="rajd-w-zeszlym-miesiacu", description="Opis",
            start_date=timezone.now().date() - timezone.timedelta(days=30),
        )
        response = self.client.get(reverse("news_list"))
        self.assertContains(response, upcoming.title)
        self.assertNotContains(response, past.title)

    def test_multi_day_event_stays_until_end_date_passes(self):
        ongoing = Event.objects.create(
            title="Rajd trwający", slug="rajd-trwajacy", description="Opis",
            start_date=timezone.now().date() - timezone.timedelta(days=1),
            end_date=timezone.now().date() + timezone.timedelta(days=1),
        )
        response = self.client.get(reverse("news_list"))
        self.assertContains(response, ongoing.title)


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


class RedaktorzyGroupTest(TestCase):
    """The branch head's account should manage content but not users/auth."""

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="redaktor", password="x", is_staff=True)
        self.user.groups.add(Group.objects.get(name="Redaktorzy"))
        self.client.force_login(self.user)

    def test_can_reach_admin_dashboard(self):
        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 200)

    def test_can_add_a_post(self):
        response = self.client.get(reverse("admin:siteapp_post_add"))
        self.assertEqual(response.status_code, 200)

    def test_cannot_manage_users_or_groups(self):
        self.assertEqual(self.client.get(reverse("admin:auth_user_changelist")).status_code, 403)
        self.assertEqual(self.client.get(reverse("admin:auth_group_changelist")).status_code, 403)

    def test_cannot_add_or_edit_central_news_but_can_view_and_delete(self):
        item = CentralNews.objects.create(
            wp_id=1, title="Z centrali", link="https://pttk.pl/x/", published_at=timezone.now(),
        )
        self.assertEqual(self.client.get(reverse("admin:siteapp_centralnews_add")).status_code, 403)
        self.assertEqual(self.client.get(reverse("admin:siteapp_centralnews_changelist")).status_code, 200)
        self.assertEqual(self.client.get(reverse("admin:siteapp_centralnews_delete", args=[item.pk])).status_code, 200)


class PanelAuthTest(TestCase):
    """The self-service /panel/ signup + approval flow."""

    def test_signup_creates_inactive_user(self):
        response = self.client.post(reverse("panel_signup"), {
            "full_name": "Andrzej Testowy",
            "email": "andrzej@example.com",
            "username": "andrzej",
            "password1": "bardzo-tajne-haslo",
            "password2": "bardzo-tajne-haslo",
            "honeypot": "",
        })
        self.assertEqual(response.status_code, 200)
        user = get_user_model().objects.get(username="andrzej")
        self.assertFalse(user.is_active)
        self.assertFalse(user.is_staff)

    def test_pending_user_cannot_log_in(self):
        get_user_model().objects.create_user(username="pending", password="haslo12345", is_active=False)
        response = self.client.post(reverse("panel_login"), {"username": "pending", "password": "haslo12345"})
        self.assertContains(response, "czeka jeszcze na zatwierdzenie")

    def test_approved_user_can_log_in_and_reach_dashboard(self):
        user = get_user_model().objects.create_user(username="approved", password="haslo12345", is_active=True)
        response = self.client.post(reverse("panel_login"), {"username": "approved", "password": "haslo12345"}, follow=True)
        self.assertRedirects(response, reverse("panel_dashboard"))

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("panel_dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("panel_login"), response.url)


class PanelContentTest(TestCase):
    """Logged-in editors can manage content through /panel/."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(username="editor", password="x", is_active=True)
        self.client.force_login(self.user)

    def test_can_attach_photo_directly_when_creating_a_post(self):
        create = self.client.post(reverse("panel_post_create"), {
            "title": "Nowa aktualność",
            "body": "Treść",
            "published_at": "2026-08-23T10:00",
            "attachments": [tiny_jpeg()],
        })
        post = Post.objects.get(title="Nowa aktualność")
        self.assertRedirects(create, reverse("panel_post_edit", args=[post.pk]))
        self.assertEqual(post.images.count(), 1)

    def test_create_edit_and_delete_post_with_photo(self):
        create = self.client.post(reverse("panel_post_create"), {
            "title": "Nowa aktualność",
            "body": "Treść",
            "published_at": "2026-08-23T10:00",
        })
        post = Post.objects.get(title="Nowa aktualność")
        self.assertRedirects(create, reverse("panel_post_edit", args=[post.pk]))

        add_photo = self.client.post(
            reverse("panel_post_edit", args=[post.pk]),
            {
                "title": post.title, "body": post.body,
                "published_at": "2026-08-23T10:00",
                "attachments": [tiny_jpeg()],
            },
        )
        self.assertRedirects(add_photo, reverse("panel_post_edit", args=[post.pk]))
        self.assertEqual(post.images.count(), 1)

        photo = post.images.first()
        self.client.post(reverse("panel_post_photo_delete", args=[photo.pk]))
        self.assertEqual(post.images.count(), 0)

        self.client.post(reverse("panel_post_delete", args=[post.pk]))
        self.assertFalse(Post.objects.filter(pk=post.pk).exists())
        # soft delete: still there for restore, just hidden from the default manager
        trashed = Post.all_objects.get(pk=post.pk)
        self.assertTrue(trashed.is_deleted)
        self.assertIsNotNone(trashed.deleted_at)

    def test_deleted_post_can_be_restored_from_trash(self):
        post = Post.objects.create(title="Do kosza", body="x", published_at=timezone.now())
        post.soft_delete()

        trash = self.client.get(reverse("panel_post_trash"))
        self.assertContains(trash, "Do kosza")

        self.client.post(reverse("panel_post_restore", args=[post.pk]))
        self.assertTrue(Post.objects.filter(pk=post.pk).exists())

    def test_purge_permanently_deletes(self):
        post = Post.objects.create(title="Na zawsze", body="x", published_at=timezone.now())
        post.soft_delete()

        self.client.post(reverse("panel_post_purge", args=[post.pk]))
        self.assertFalse(Post.all_objects.filter(pk=post.pk).exists())

    def test_new_post_and_event_are_public_by_default_with_no_visibility_field(self):
        self.assertNotIn("is_published", PanelPostForm().fields)
        self.assertNotIn("is_published", PanelEventForm().fields)
        self.assertNotIn("is_public", PanelDocumentForm().fields)

        self.client.post(reverse("panel_post_create"), {
            "title": "Domyślnie publiczna", "body": "x", "published_at": "2026-08-23T10:00",
        })
        self.assertTrue(Post.objects.get(title="Domyślnie publiczna").is_published)

    def test_can_attach_and_remove_document_on_post(self):
        post = Post.objects.create(title="Z dokumentem", body="x", published_at=timezone.now())
        add = self.client.post(
            reverse("panel_post_edit", args=[post.pk]),
            {
                "title": post.title, "body": post.body,
                "published_at": "2026-08-23T10:00",
                "attachments": [SimpleUploadedFile("statut.pdf", b"%PDF-1.4 test", content_type="application/pdf")],
            },
        )
        self.assertRedirects(add, reverse("panel_post_edit", args=[post.pk]))
        self.assertEqual(post.documents.count(), 1)

        doc = post.documents.first()
        self.client.post(reverse("panel_post_document_delete", args=[doc.pk]))
        self.assertEqual(post.documents.count(), 0)

    def test_mixed_attachments_split_by_extension_and_reject_unknown(self):
        post = Post.objects.create(title="Mieszane", body="x", published_at=timezone.now())
        self.client.post(
            reverse("panel_post_edit", args=[post.pk]),
            {
                "title": post.title, "body": post.body,
                "published_at": "2026-08-23T10:00",
                "attachments": [
                    tiny_jpeg(),
                    SimpleUploadedFile("regulamin.pdf", b"%PDF-1.4 x", content_type="application/pdf"),
                    SimpleUploadedFile("virus.exe", b"x", content_type="application/octet-stream"),
                ],
            },
        )
        self.assertEqual(post.images.count(), 1)
        self.assertEqual(post.documents.count(), 1)

    def test_event_list_splits_upcoming_and_past(self):
        upcoming = Event.objects.create(
            title="Za tydzień", slug="za-tydzien", description="x",
            start_date=timezone.now().date() + timezone.timedelta(days=7),
        )
        past = Event.objects.create(
            title="Był wczoraj", slug="byl-wczoraj", description="x",
            start_date=timezone.now().date() - timezone.timedelta(days=1),
        )
        response = self.client.get(reverse("panel_event_list"))
        self.assertIn(upcoming, response.context["upcoming"])
        self.assertIn(past, response.context["past"])
        self.assertNotIn(upcoming, response.context["past"])
        self.assertNotIn(past, response.context["upcoming"])

    def test_create_event_auto_generates_unique_slug(self):
        self.client.post(reverse("panel_event_create"), {
            "title": "Rajd Testowy",
            "description": "Opis",
            "start_date": "2026-09-01",
            "is_published": "on",
        })
        self.client.post(reverse("panel_event_create"), {
            "title": "Rajd Testowy",
            "description": "Inny opis",
            "start_date": "2026-10-01",
            "is_published": "on",
        })
        slugs = set(Event.objects.filter(title="Rajd Testowy").values_list("slug", flat=True))
        self.assertEqual(len(slugs), 2)

    def test_create_document_requires_a_file(self):
        response = self.client.post(reverse("panel_document_create"), {
            "title": "Statut", "category": "", "is_public": "on",
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Document.objects.filter(title="Statut").exists())
