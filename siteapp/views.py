from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.contrib import messages
from django.core.mail import EmailMessage
from django.conf import settings
from .models import Post, PostImage, Event, Person, Document, FbAlbum, FbPhoto, HeroImage
from .forms import ContactForm

import logging
logger = logging.getLogger(__name__)

def index(request):
    news = Post.objects.filter(is_published=True).prefetch_related('images').order_by('-published_at')[:6]
    hero = HeroImage.objects.filter(is_active=True).order_by('order')[:5]
    return render(request, 'index.html', {'news': news, 'hero': hero})

def news_list(request):
    items = Post.objects.filter(is_published=True).prefetch_related('images').order_by('-published_at')
    return render(request, 'news/list.html', {'items': items})

def news_detail(request, pk):
    item = get_object_or_404(Post.objects.prefetch_related('images'), pk=pk, is_published=True)
    return render(request, 'news/detail.html', {'item': item})

def event_list(request):
    items = Event.objects.filter(is_published=True).order_by('start_date')
    return render(request, 'events/list.html', {'items': items})

def event_detail(request, slug):
    item = get_object_or_404(Event, slug=slug, is_published=True)
    photos = FbPhoto.objects.filter(album__isnull=False)[:0]
    return render(request, 'events/detail.html', {'item': item, 'photos': photos})

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
    albums = FbAlbum.objects.order_by('-updated')
    return render(request, 'gallery/albums.html', {'albums': albums})

def gallery_album_detail(request, album_id):
    album = get_object_or_404(FbAlbum, fb_album_id=album_id)
    photos = FbPhoto.objects.filter(album=album).order_by('-created_time')
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
