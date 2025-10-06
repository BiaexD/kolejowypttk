import os
import requests
from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime
from django.utils.timezone import make_aware
from siteapp.models import Post, FbAlbum, FbPhoto

BASE = "https://graph.facebook.com/v19.0"

def tz_aware(dt_str):
    if not dt_str:
        return None
    dt = parse_datetime(dt_str)
    if dt and dt.tzinfo is None:
        return make_aware(dt)
    return dt

class Command(BaseCommand):
    help = "Importuje posty i galerię (albumy + zdjęcia) z Facebook Page do lokalnej bazy (URL-e, bez plików)."

    def add_arguments(self, parser):
        parser.add_argument("--limit-posts", type=int, default=10, help="Ile najnowszych postów pobrać.")
        parser.add_argument("--limit-albums", type=int, default=10, help="Ile najnowszych albumów pobrać.")
        parser.add_argument("--limit-photos", type=int, default=50, help="Ile zdjęć na album pobrać.")

    def handle(self, *args, **opts):
        page_id = os.getenv("FB_PAGE_ID")
        token = os.getenv("FB_ACCESS_TOKEN")
        if not page_id or not token:
            self.stderr.write(self.style.ERROR("Brak FB_PAGE_ID albo FB_ACCESS_TOKEN w .env"))
            return

        try:
            self.import_posts(page_id, token, opts["limit_posts"])
            self.import_albums_and_photos(page_id, token, opts["limit_albums"], opts["limit_photos"])
        except requests.HTTPError as e:
            self.stderr.write(self.style.ERROR(f"HTTPError: {e}"))
        except requests.RequestException as e:
            self.stderr.write(self.style.ERROR(f"Network error: {e}"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Unexpected error: {e}"))

    # ──────────────────────────────────────────
    # POSTY → Post (source=FACEBOOK)
    # ──────────────────────────────────────────
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

    # ──────────────────────────────────────────
    # ALBUMY + ZDJĘCIA → FbAlbum, FbPhoto
    # ──────────────────────────────────────────
    def import_albums_and_photos(self, page_id, token, limit_albums, limit_photos):
        albums_url = f"{BASE}/{page_id}/albums"
        params = {
            "fields": "id,name,count,cover_photo",
            "access_token": token,
            "limit": limit_albums,
        }
        ra = requests.get(albums_url, params=params, timeout=20)
        ra.raise_for_status()
        albums = ra.json().get("data", [])

        total_photos = 0
        for a in albums:
            alb, _ = FbAlbum.objects.update_or_create(
                fb_album_id=a.get("id"),
                defaults=dict(
                    name=a.get("name") or "",
                    count=a.get("count") or 0,
                    cover_photo_id=(a.get("cover_photo") or {}).get("id", ""),
                ),
            )

            photos_url = f"{BASE}/{alb.fb_album_id}/photos"
            photos_params = {
                "fields": "id,images,created_time,permalink_url,name",
                "access_token": token,
                "limit": limit_photos,
            }
            rp = requests.get(photos_url, params=photos_params, timeout=20)
            rp.raise_for_status()
            photos = rp.json().get("data", [])

            added, updated = 0, 0
            for ph in photos:
                images = ph.get("images") or []
                big = images[0]["source"] if images else ""
                thumb = images[-1]["source"] if images else ""

                _, is_created = FbPhoto.objects.update_or_create(
                    fb_photo_id=ph.get("id"),
                    defaults=dict(
                        album=alb,
                        created_time=tz_aware(ph.get("created_time")),
                        permalink_url=ph.get("permalink_url") or "",
                        image_url=big,
                        thumb_url=thumb,
                        caption=ph.get("name") or "",
                    ),
                )
                if is_created:
                    added += 1
                else:
                    updated += 1
            total_photos += added
            self.stdout.write(self.style.SUCCESS(
                f"Album '{alb.name or alb.fb_album_id}': dodano zdjęć {added}, zaktualizowano {updated}"
            ))

        self.stdout.write(self.style.SUCCESS(f"Zdjęcia ogółem dodane: {total_photos}"))
