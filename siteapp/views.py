from datetime import time

from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.contrib import messages
from django.core.mail import EmailMessage
from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from .models import Post, PostImage, Event, Person, Document, HeroImage, CentralNews
from .event_utils import event_time_split
from .forms import ContactForm
from .geocoding import geocode_address, get_route, ORS_PROFILES

import logging
logger = logging.getLogger(__name__)


def _page_nav_urls(request, page_obj, param):
    """Buduje adresy poprzedniej/następnej strony (zachowując resztę query stringa), albo None gdy brak."""
    def build(page_number):
        if not page_number:
            return None
        qd = request.GET.copy()
        qd[param] = page_number
        return f"{request.path}?{qd.urlencode()}"

    prev_number = page_obj.previous_page_number() if page_obj.has_previous() else None
    next_number = page_obj.next_page_number() if page_obj.has_next() else None
    return build(prev_number), build(next_number)


def index(request):
    news = Post.objects.filter(is_published=True).prefetch_related('images').order_by('-published_at')[:6]
    hero = HeroImage.objects.filter(is_active=True).order_by('order')[:5]
    return render(request, 'index.html', {'news': news, 'hero': hero})

def news_list(request):
    today = timezone.now().date()
    is_upcoming = Q(end_date__gte=today) | (Q(end_date__isnull=True) & Q(start_date__gte=today))

    posts = list(Post.objects.filter(is_published=True).prefetch_related('images'))
    upcoming_events = list(
        Event.objects.filter(is_published=True).filter(is_upcoming).prefetch_related('photos')
    )

    def feed_date(item):
        if isinstance(item, Event):
            return timezone.make_aware(timezone.datetime.combine(item.start_date, time.min))
        return item.published_at

    own_items = sorted(posts + upcoming_events, key=feed_date, reverse=True)
    own_page = Paginator(own_items, 3).get_page(request.GET.get('own_page'))

    central_items = CentralNews.objects.all()
    central_page = Paginator(central_items, 3).get_page(request.GET.get('central_page'))

    own_prev_url, own_next_url = _page_nav_urls(request, own_page, 'own_page')
    central_prev_url, central_next_url = _page_nav_urls(request, central_page, 'central_page')

    return render(request, 'news/list.html', {
        'own_page': own_page,
        'central_page': central_page,
        'own_prev_url': own_prev_url,
        'own_next_url': own_next_url,
        'central_prev_url': central_prev_url,
        'central_next_url': central_next_url,
    })

def news_detail(request, pk):
    item = get_object_or_404(Post.objects.prefetch_related('images'), pk=pk, is_published=True)
    return render(request, 'news/detail.html', {'item': item})

def event_list(request):
    upcoming, past = event_time_split(Event.objects.filter(is_published=True))
    upcoming_page = Paginator(upcoming, 10).get_page(request.GET.get('upcoming_page'))
    past_page = Paginator(past, 10).get_page(request.GET.get('past_page'))

    upcoming_prev_url, upcoming_next_url = _page_nav_urls(request, upcoming_page, 'upcoming_page')
    past_prev_url, past_next_url = _page_nav_urls(request, past_page, 'past_page')

    return render(request, 'events/list.html', {
        'upcoming_page': upcoming_page,
        'past_page': past_page,
        'upcoming_prev_url': upcoming_prev_url,
        'upcoming_next_url': upcoming_next_url,
        'past_prev_url': past_prev_url,
        'past_next_url': past_next_url,
    })

def event_detail(request, slug):
    item = get_object_or_404(Event.objects.prefetch_related('photos'), slug=slug, is_published=True)
    return render(request, 'events/detail.html', {'item': item})


def event_route(request, slug):
    """Zwraca wyznaczoną trasę (JSON) od podanego punktu startu do miejsca wydarzenia."""
    item = get_object_or_404(Event, slug=slug, is_published=True)
    if item.location_lat is None or item.location_lng is None:
        return JsonResponse({"error": "Wydarzenie nie ma ustawionej lokalizacji."}, status=400)

    profile = request.GET.get("profile", "")
    if profile not in ORS_PROFILES:
        return JsonResponse({"error": "Nieprawidłowy środek transportu."}, status=400)

    start_lat = request.GET.get("start_lat")
    start_lng = request.GET.get("start_lng")
    start_address = request.GET.get("start_address", "").strip()

    if start_lat and start_lng:
        try:
            start_lat, start_lng = float(start_lat), float(start_lng)
        except ValueError:
            return JsonResponse({"error": "Nieprawidłowe współrzędne startu."}, status=400)
    elif start_address:
        coords = geocode_address(start_address)
        if coords is None:
            return JsonResponse({"error": "Nie udało się znaleźć podanego adresu."}, status=400)
        start_lat, start_lng = coords
    else:
        return JsonResponse({"error": "Podaj punkt startowy."}, status=400)

    route = get_route(start_lat, start_lng, item.location_lat, item.location_lng, profile)
    if route is None:
        return JsonResponse({"error": "Nie udało się wyznaczyć trasy."}, status=502)

    return JsonResponse(route)


def board(request):
    people = Person.objects.all().order_by("body", "order", "role", "name")

    groups = {
        "zarzad": [],
        "sad": [],
        "komisja": [],
    }
    for p in people:
        groups[p.body].append(p)

    body_titles = dict(Person.BODY_CHOICES)

    return render(
        request,
        "people/board.html",
        {
            "groups": groups,
            "body_titles": body_titles,
        },
    )

def docs_list(request):
    docs = Document.objects.filter(is_public=True).order_by('category','title')
    return render(request, 'docs/list.html', {'docs': docs})

def gallery_albums(request):
    albums = (
        Event.objects.filter(is_published=True, photos__isnull=False)
        .distinct()
        .order_by('-start_date')
    )
    page_obj = Paginator(albums, 9).get_page(request.GET.get('page'))
    prev_url, next_url = _page_nav_urls(request, page_obj, 'page')
    return render(request, 'gallery/albums.html', {
        'albums': page_obj.object_list,
        'page_obj': page_obj,
        'prev_url': prev_url,
        'next_url': next_url,
    })

def gallery_album_detail(request, slug):
    album = get_object_or_404(Event.objects.prefetch_related('photos'), slug=slug, is_published=True)
    photos = album.photos.all()
    return render(request, 'gallery/album_detail.html', {'album': album, 'photos': photos})

def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data["name"]
            email = form.cleaned_data["email"]
            message = form.cleaned_data["message"]

            subject = f"[{settings.SITE_NAME}] Wiadomość z formularza kontaktowego"
            body = (
                f"Imię i nazwisko: {name}\n"
                f"Email: {email}\n\n"
                f"Wiadomość:\n{message}\n"
            )

            msg = EmailMessage(
                subject=subject,
                body=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[settings.CONTACT_TO_EMAIL],
                reply_to=[email],  # mega ważne: "Odpowiedz" idzie do nadawcy
            )

            try:
                msg.send(fail_silently=False)
                messages.success(request, "Dziękujemy! Wiadomość została wysłana.")
            except Exception:
                messages.error(request, "Ups — nie udało się wysłać wiadomości. Spróbuj ponownie później.")

            return redirect("contact")
    else:
        form = ContactForm()
    return render(request, 'contact.html', {'form': form})


def historia(request):
    return render(request, "historia.html")

def odznaki(request):
    return render(request, "odznaki.html")

def robots_txt(request):
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /admin/",
        f"Sitemap: {request.scheme}://{request.get_host()}/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")
