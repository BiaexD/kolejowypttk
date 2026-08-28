import html
import re

import requests
from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime
from django.utils.timezone import make_aware

from siteapp.models import CentralNews

API_URL = "https://wko.pttk.pl/wp-json/wp/v2/posts"


def clean_text(raw):
    return html.unescape(re.sub(r"<[^>]+>", "", raw or "")).strip()


class Command(BaseCommand):
    help = "Importuje najnowsze aktualności z wko.pttk.pl (Wielkopolska Korporacja Oddziałów PTTK) przez WP REST API."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=20, help="Ile najnowszych aktualności pobrać.")

    def handle(self, *args, **opts):
        params = {
            "per_page": opts["limit"],
            "_embed": "wp:featuredmedia",
            "orderby": "date",
            "order": "desc",
        }
        try:
            r = requests.get(API_URL, params=params, timeout=20)
            r.raise_for_status()
        except requests.RequestException as e:
            self.stderr.write(self.style.ERROR(f"Błąd pobierania z wko.pttk.pl: {e}"))
            return

        added, updated = 0, 0
        for p in r.json():
            published = parse_datetime(p["date"])
            if published and published.tzinfo is None:
                published = make_aware(published)

            image_url = ""
            media = (p.get("_embedded") or {}).get("wp:featuredmedia")
            if media:
                image_url = media[0].get("source_url", "")

            obj, is_created = CentralNews.objects.update_or_create(
                source=CentralNews.SOURCE_WKO,
                wp_id=p["id"],
                defaults=dict(
                    title=clean_text(p["title"]["rendered"]),
                    excerpt=clean_text(p["excerpt"]["rendered"])[:400],
                    link=p["link"],
                    image_url=image_url,
                    published_at=published,
                ),
            )
            if is_created:
                added += 1
            else:
                updated += 1

        self.stdout.write(self.style.SUCCESS(f"WKO PTTK → dodano: {added}, zaktualizowano: {updated}"))
