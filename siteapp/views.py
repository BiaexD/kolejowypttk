from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.contrib import messages
from .models import Post, Event, Person, Document, FbAlbum, FbPhoto, HeroImage
from .forms import ContactForm

def index(request):
    news   = Post.objects.filter(is_published=True).order_by('-published_at')[:4]
    events = Event.objects.filter(is_published=True, start_date__gte=timezone.localdate()).order_by('start_date')[:3]
    albums = FbAlbum.objects.order_by('-updated')[:6]
    hero   = HeroImage.objects.filter(is_active=True).order_by('order')[:5]
    return render(request, 'index.html', {'news': news, 'events': events, 'albums': albums, 'hero': hero})

def news_list(request):
    items = Post.objects.filter(is_published=True).order_by('-published_at')
    return render(request, 'news/list.html', {'items': items})

def news_detail(request, pk):
    item = get_object_or_404(Post, pk=pk, is_published=True)
    return render(request, 'news/detail.html', {'item': item})

def event_list(request):
    items = Event.objects.filter(is_published=True).order_by('start_date')
    return render(request, 'events/list.html', {'items': items})

def event_detail(request, slug):
    item = get_object_or_404(Event, slug=slug, is_published=True)
    photos = FbPhoto.objects.filter(album__isnull=False)[:0]
    return render(request, 'events/detail.html', {'item': item, 'photos': photos})

def board(request):
    people = Person.objects.all()
    return render(request, 'people/board.html', {'people': people})

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
            messages.success(request, "Dziękujemy za wiadomość!")
            return redirect('contact')
    else:
        form = ContactForm()
    return render(request, 'contact.html', {'form': form})


def historia(request):
    return render(request, "historia.html")

def odznaki(request):
    return render(request, "odznaki.html")
