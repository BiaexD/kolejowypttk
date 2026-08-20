import os
import requests
from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime
from django.utils.timezone import make_aware
from siteapp.models import Post

BASE = "https://graph.facebook.com/v19.0"

def tz_aware(dt_str):
    if not dt_str:
        return None
    dt = parse_datetime(dt_str)
    if dt and dt.tzinfo is None:
        return make_aware(dt)
    return dt

class Command(BaseCommand):
    help = "Importuje posty z Facebook Page do lokalnej bazy jako Aktualności (URL zdjęcia, bez pliku)."

    def add_arguments(self, parser):
        parser.add_argument("--limit-posts", type=int, default=10, help="Ile najnowszych postów pobrać.")

    def handle(self, *args, **opts):
        page_id = os.getenv("FB_PAGE_ID")
        token = os.getenv("FB_ACCESS_TOKEN")
        if not page_id or not token:
            self.stderr.write(self.style.ERROR("Brak FB_PAGE_ID albo FB_ACCESS_TOKEN w .env"))
            return

        try:
            self.import_posts(page_id, token, opts["limit_posts"])
        except requests.HTTPError as e:
            self.stderr.write(self.style.ERROR(f"HTTPError: {e}"))
        except requests.RequestException as e:
            self.stderr.write(self.style.ERROR(f"Network error: {e}"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Unexpected error: {e}"))

    def import_posts(self, page_id, token, limit):
        url = f"{BASE}/{page_id}/posts"
        params = {
            "fields": "id,message,permalink_url,full_picture,created_time",
            "access_token": token,
            "limit": limit,
        }
        r = requests.get(url, params=params, timeout=20)
        r.raise_for_status()
        data = r.json().get("data", [])

        added, updated = 0, 0
        for p in data:
            fb_id = p.get("id") or ""
            created = tz_aware(p.get("created_time"))
            title = (p.get("message") or "").splitlines()[0][:180] if p.get("message") else ""
            body = p.get("message") or ""
            image_url = p.get("full_picture") or ""
            perma = p.get("permalink_url") or ""

            obj, is_created = Post.objects.update_or_create(
                fb_post_id=fb_id,
                defaults=dict(
                    source="FACEBOOK",
                    title=title,
                    body=body,
                    image_url=image_url,
                    fb_perma=perma,
                    published_at=created,
                    is_published=True,
                ),
            )
            if is_created:
                added += 1
            else:
                updated += 1

        self.stdout.write(self.style.SUCCESS(f"Posty FB → dodano: {added}, zaktualizowano: {updated}"))
