import time

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.utils.text import slugify
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from .event_utils import event_time_split
from .geocoding import geocode_address
from .models import (
    Post, PostImage, PostDocument, Event, EventPhoto, EventDocument,
    Person, Document, HeroImage,
)
from .panel_forms import (
    PanelSignupForm, PanelLoginForm,
    PanelPostForm, PanelEventForm,
    PanelPersonForm, PanelDocumentForm, PanelHeroImageForm,
)

IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp"}
DOCUMENT_EXTENSIONS = {"pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "odt"}
ATTACHMENTS_HINT = "Dozwolone: JPG, PNG, GIF, WEBP (zdjęcia), PDF, DOC, DOCX, XLS, XLSX, PPT, PPTX, ODT (dokumenty)."


def _file_extension(uploaded_file):
    name = uploaded_file.name
    return name.rsplit(".", 1)[-1].lower() if "." in name else ""


def _save_attachments(request, files, image_model, doc_model, parent_field, parent_obj):
    """Jedno pole 'Załączniki' w formularzu — rozdzielamy zdjęcia od dokumentów po rozszerzeniu."""
    added_images = added_docs = 0
    for f in files:
        ext = _file_extension(f)
        if ext in IMAGE_EXTENSIONS:
            image_model.objects.create(**{parent_field: parent_obj, "image": f})
            added_images += 1
        elif ext in DOCUMENT_EXTENSIONS:
            doc_model.objects.create(**{parent_field: parent_obj, "file": f, "title": f.name})
            added_docs += 1
        else:
            messages.error(request, f"Pominięto plik „{f.name}” — nieobsługiwane rozszerzenie.")
    if added_images or added_docs:
        messages.success(request, f"Dodano załączniki: {added_images} zdjęć, {added_docs} dokumentów.")


class PanelLoginView(LoginView):
    template_name = 'panel/login.html'
    authentication_form = PanelLoginForm
    redirect_authenticated_user = True


class PanelLogoutView(LogoutView):
    pass


def panel_signup(request):
    if request.method == 'POST':
        form = PanelSignupForm(request.POST)
        if form.is_valid():
            form.save()
            return render(request, 'panel/signup_done.html')
    else:
        form = PanelSignupForm()
    return render(request, 'panel/signup.html', {'form': form})


class PanelBaseView(LoginRequiredMixin):
    pass


class SoftDeleteView(PanelBaseView, DeleteView):
    """'Usuń' w panelu nigdy nie kasuje na stałe — przenosi do kosza."""
    template_name = 'panel/confirm_delete.html'
    list_url_name = None

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['back_url'] = reverse(self.list_url_name)
        ctx['label'] = str(self.object)
        return ctx

    def form_valid(self, form):
        success_url = self.get_success_url()
        self.object.soft_delete()
        return HttpResponseRedirect(success_url)


@login_required
def panel_dashboard(request):
    return render(request, 'panel/dashboard.html')


# ---------- Kosz (wspólne dla wszystkich sekcji) ----------

def _trash_list(request, model, section_title, list_url_name, restore_url_name, purge_url_name):
    items = model.all_objects.filter(is_deleted=True).order_by('-deleted_at')
    return render(request, 'panel/trash_list.html', {
        'items': items,
        'section_title': section_title,
        'list_url': reverse(list_url_name),
        'restore_url_name': restore_url_name,
        'purge_url_name': purge_url_name,
    })


def _restore(request, model, pk, trash_url_name):
    obj = get_object_or_404(model.all_objects, pk=pk)
    if request.method == 'POST':
        obj.restore()
        messages.success(request, "Przywrócono.")
    return redirect(trash_url_name)


def _purge(request, model, pk, trash_url_name):
    obj = get_object_or_404(model.all_objects, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, "Usunięto na zawsze.")
        return redirect(trash_url_name)
    return render(request, 'panel/confirm_delete.html', {
        'label': str(obj), 'back_url': reverse(trash_url_name), 'permanent': True,
    })


# ---------- Aktualności ----------

class PanelPostListView(PanelBaseView, ListView):
    model = Post
    template_name = 'panel/post_list.html'
    context_object_name = 'posts'
    ordering = ['-published_at']


class PanelPostCreateView(PanelBaseView, CreateView):
    model = Post
    form_class = PanelPostForm
    template_name = 'panel/post_form.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['attachments_hint'] = ATTACHMENTS_HINT
        return ctx

    def form_valid(self, form):
        self.object = form.save()
        _save_attachments(self.request, self.request.FILES.getlist('attachments'), PostImage, PostDocument, 'post', self.object)
        messages.success(self.request, "Aktualność dodana.")
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('panel_post_edit', args=[self.object.pk])


class PanelPostUpdateView(PanelBaseView, UpdateView):
    model = Post
    form_class = PanelPostForm
    template_name = 'panel/post_form.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['photos'] = self.object.images.all()
        ctx['documents'] = self.object.documents.all()
        ctx['attachments_hint'] = ATTACHMENTS_HINT
        return ctx

    def form_valid(self, form):
        self.object = form.save()
        _save_attachments(self.request, self.request.FILES.getlist('attachments'), PostImage, PostDocument, 'post', self.object)
        messages.success(self.request, "Zmiany zapisane.")
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('panel_post_edit', args=[self.object.pk])


class PanelPostDeleteView(SoftDeleteView):
    model = Post
    success_url = reverse_lazy('panel_post_list')
    list_url_name = 'panel_post_list'


@login_required
def panel_post_trash(request):
    return _trash_list(request, Post, "Aktualności", 'panel_post_list', 'panel_post_restore', 'panel_post_purge')


@login_required
def panel_post_restore(request, pk):
    return _restore(request, Post, pk, 'panel_post_trash')


@login_required
def panel_post_purge(request, pk):
    return _purge(request, Post, pk, 'panel_post_trash')


@login_required
def panel_post_photo_delete(request, pk):
    photo = get_object_or_404(PostImage, pk=pk)
    post_pk = photo.post_id
    if request.method == 'POST':
        photo.image.delete(save=False)
        photo.delete()
        messages.success(request, "Zdjęcie usunięte.")
    return redirect('panel_post_edit', pk=post_pk)


@login_required
def panel_post_document_delete(request, pk):
    doc = get_object_or_404(PostDocument, pk=pk)
    post_pk = doc.post_id
    if request.method == 'POST':
        doc.file.delete(save=False)
        doc.delete()
        messages.success(request, "Dokument usunięty.")
    return redirect('panel_post_edit', pk=post_pk)


# ---------- Wydarzenia ----------

@login_required
def panel_event_list(request):
    upcoming, past = event_time_split()
    return render(request, 'panel/event_list.html', {'upcoming': upcoming, 'past': past})


def _geocode_event_place(request, obj, field, lat_field, lng_field, label):
    """Geokoduje pole tekstowe adresu wydarzenia i zapisuje wynik w lat/lng, albo je czyści."""
    value = getattr(obj, field)
    if not value:
        setattr(obj, lat_field, None)
        setattr(obj, lng_field, None)
        return

    coords = geocode_address(value)
    if coords:
        setattr(obj, lat_field, coords[0])
        setattr(obj, lng_field, coords[1])
    else:
        setattr(obj, lat_field, None)
        setattr(obj, lng_field, None)
        messages.warning(
            request,
            f"Nie udało się automatycznie zlokalizować adresu ({label}) — mapa nie pojawi się na "
            "stronie wydarzenia. Spróbuj podać dokładniejszy adres (ulica, numer, miejscowość).",
        )


class PanelEventCreateView(PanelBaseView, CreateView):
    model = Event
    form_class = PanelEventForm
    template_name = 'panel/event_form.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['attachments_hint'] = ATTACHMENTS_HINT
        return ctx

    def form_valid(self, form):
        base = slugify(form.instance.title)[:200] or 'wydarzenie'
        slug = base
        i = 2
        while Event.objects.filter(slug=slug).exists():
            slug = f"{base}-{i}"
            i += 1
        form.instance.slug = slug
        self.object = form.save(commit=False)
        _geocode_event_place(self.request, self.object, 'location', 'location_lat', 'location_lng', 'miejsce rozpoczęcia')
        if self.object.end_location and self.object.end_location.strip().lower() != (self.object.location or '').strip().lower():
            time.sleep(1)  # Nominatim: max 1 zapytanie/s, unikamy blokady drugiego wywołania w tym samym żądaniu
            _geocode_event_place(self.request, self.object, 'end_location', 'end_location_lat', 'end_location_lng', 'miejsce zakończenia')
        else:
            self.object.end_location_lat = None
            self.object.end_location_lng = None
        self.object.save()
        _save_attachments(self.request, self.request.FILES.getlist('attachments'), EventPhoto, EventDocument, 'event', self.object)
        messages.success(self.request, "Wydarzenie dodane.")
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('panel_event_edit', args=[self.object.pk])


class PanelEventUpdateView(PanelBaseView, UpdateView):
    model = Event
    form_class = PanelEventForm
    template_name = 'panel/event_form.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['photos'] = self.object.photos.all()
        ctx['documents'] = self.object.documents.all()
        ctx['attachments_hint'] = ATTACHMENTS_HINT
        return ctx

    def form_valid(self, form):
        location_changed = 'location' in form.changed_data
        end_location_changed = 'end_location' in form.changed_data
        self.object = form.save(commit=False)

        # Geokodujemy też wtedy, gdy tekst się nie zmienił, ale poprzednia próba
        # nie powiodła się (np. przez limit zapytań Nominatim) — inaczej trwale
        # zabrakłoby mapy, dopóki ktoś ręcznie nie zmieniłby adresu.
        location_needs_geocode = bool(self.object.location) and (location_changed or self.object.location_lat is None)
        if location_needs_geocode:
            _geocode_event_place(self.request, self.object, 'location', 'location_lat', 'location_lng', 'miejsce rozpoczęcia')
        elif not self.object.location:
            self.object.location_lat = None
            self.object.location_lng = None

        end_location_is_distinct = bool(self.object.end_location) and self.object.end_location.strip().lower() != (self.object.location or '').strip().lower()
        if end_location_is_distinct:
            end_location_needs_geocode = location_changed or end_location_changed or self.object.end_location_lat is None
            if end_location_needs_geocode:
                if location_needs_geocode:
                    time.sleep(1)  # Nominatim: max 1 zapytanie/s, unikamy blokady drugiego wywołania w tym samym żądaniu
                _geocode_event_place(self.request, self.object, 'end_location', 'end_location_lat', 'end_location_lng', 'miejsce zakończenia')
        else:
            self.object.end_location_lat = None
            self.object.end_location_lng = None

        self.object.save()
        _save_attachments(self.request, self.request.FILES.getlist('attachments'), EventPhoto, EventDocument, 'event', self.object)
        messages.success(self.request, "Zmiany zapisane.")
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('panel_event_edit', args=[self.object.pk])


class PanelEventDeleteView(SoftDeleteView):
    model = Event
    success_url = reverse_lazy('panel_event_list')
    list_url_name = 'panel_event_list'


@login_required
def panel_event_trash(request):
    return _trash_list(request, Event, "Wydarzenia", 'panel_event_list', 'panel_event_restore', 'panel_event_purge')


@login_required
def panel_event_restore(request, pk):
    return _restore(request, Event, pk, 'panel_event_trash')


@login_required
def panel_event_purge(request, pk):
    return _purge(request, Event, pk, 'panel_event_trash')


@login_required
def panel_event_photo_delete(request, pk):
    photo = get_object_or_404(EventPhoto, pk=pk)
    event_pk = photo.event_id
    if request.method == 'POST':
        photo.image.delete(save=False)
        photo.delete()
        messages.success(request, "Zdjęcie usunięte.")
    return redirect('panel_event_edit', pk=event_pk)


@login_required
def panel_event_document_delete(request, pk):
    doc = get_object_or_404(EventDocument, pk=pk)
    event_pk = doc.event_id
    if request.method == 'POST':
        doc.file.delete(save=False)
        doc.delete()
        messages.success(request, "Dokument usunięty.")
    return redirect('panel_event_edit', pk=event_pk)


# ---------- Władze ----------

class PanelPersonListView(PanelBaseView, ListView):
    model = Person
    template_name = 'panel/person_list.html'
    context_object_name = 'people'
    ordering = ['body', 'order', 'name']


class PanelPersonCreateView(PanelBaseView, CreateView):
    model = Person
    form_class = PanelPersonForm
    template_name = 'panel/person_form.html'
    success_url = reverse_lazy('panel_person_list')

    def form_valid(self, form):
        messages.success(self.request, "Osoba dodana.")
        return super().form_valid(form)


class PanelPersonUpdateView(PanelBaseView, UpdateView):
    model = Person
    form_class = PanelPersonForm
    template_name = 'panel/person_form.html'
    success_url = reverse_lazy('panel_person_list')

    def form_valid(self, form):
        messages.success(self.request, "Zmiany zapisane.")
        return super().form_valid(form)


class PanelPersonDeleteView(SoftDeleteView):
    model = Person
    success_url = reverse_lazy('panel_person_list')
    list_url_name = 'panel_person_list'


@login_required
def panel_person_trash(request):
    return _trash_list(request, Person, "Władze", 'panel_person_list', 'panel_person_restore', 'panel_person_purge')


@login_required
def panel_person_restore(request, pk):
    return _restore(request, Person, pk, 'panel_person_trash')


@login_required
def panel_person_purge(request, pk):
    return _purge(request, Person, pk, 'panel_person_trash')


# ---------- Dokumenty ----------

class PanelDocumentListView(PanelBaseView, ListView):
    model = Document
    template_name = 'panel/document_list.html'
    context_object_name = 'documents'
    ordering = ['category', 'title']


class PanelDocumentCreateView(PanelBaseView, CreateView):
    model = Document
    form_class = PanelDocumentForm
    template_name = 'panel/document_form.html'
    success_url = reverse_lazy('panel_document_list')

    def form_valid(self, form):
        messages.success(self.request, "Dokument dodany.")
        return super().form_valid(form)


class PanelDocumentUpdateView(PanelBaseView, UpdateView):
    model = Document
    form_class = PanelDocumentForm
    template_name = 'panel/document_form.html'
    success_url = reverse_lazy('panel_document_list')

    def form_valid(self, form):
        messages.success(self.request, "Zmiany zapisane.")
        return super().form_valid(form)


class PanelDocumentDeleteView(SoftDeleteView):
    model = Document
    success_url = reverse_lazy('panel_document_list')
    list_url_name = 'panel_document_list'


@login_required
def panel_document_trash(request):
    return _trash_list(request, Document, "Dokumenty", 'panel_document_list', 'panel_document_restore', 'panel_document_purge')


@login_required
def panel_document_restore(request, pk):
    return _restore(request, Document, pk, 'panel_document_trash')


@login_required
def panel_document_purge(request, pk):
    return _purge(request, Document, pk, 'panel_document_trash')


# ---------- Hero ----------

class PanelHeroListView(PanelBaseView, ListView):
    model = HeroImage
    template_name = 'panel/hero_list.html'
    context_object_name = 'slides'
    ordering = ['order', 'created']


class PanelHeroCreateView(PanelBaseView, CreateView):
    model = HeroImage
    form_class = PanelHeroImageForm
    template_name = 'panel/hero_form.html'
    success_url = reverse_lazy('panel_hero_list')

    def form_valid(self, form):
        messages.success(self.request, "Slajd dodany.")
        return super().form_valid(form)


class PanelHeroUpdateView(PanelBaseView, UpdateView):
    model = HeroImage
    form_class = PanelHeroImageForm
    template_name = 'panel/hero_form.html'
    success_url = reverse_lazy('panel_hero_list')

    def form_valid(self, form):
        messages.success(self.request, "Zmiany zapisane.")
        return super().form_valid(form)


class PanelHeroDeleteView(SoftDeleteView):
    model = HeroImage
    success_url = reverse_lazy('panel_hero_list')
    list_url_name = 'panel_hero_list'


@login_required
def panel_hero_trash(request):
    return _trash_list(request, HeroImage, "Zdjęcie główne", 'panel_hero_list', 'panel_hero_restore', 'panel_hero_purge')


@login_required
def panel_hero_restore(request, pk):
    return _restore(request, HeroImage, pk, 'panel_hero_trash')


@login_required
def panel_hero_purge(request, pk):
    return _purge(request, HeroImage, pk, 'panel_hero_trash')
