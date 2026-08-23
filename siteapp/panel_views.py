from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.utils.text import slugify
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from .models import Post, PostImage, Event, EventPhoto, Person, Document, HeroImage
from .panel_forms import (
    PanelSignupForm, PanelLoginForm,
    PanelPostForm, PanelPostImageForm,
    PanelEventForm, PanelEventPhotoForm,
    PanelPersonForm, PanelDocumentForm, PanelHeroImageForm,
)


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


@login_required
def panel_dashboard(request):
    return render(request, 'panel/dashboard.html')


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

    def get_success_url(self):
        messages.success(self.request, "Aktualność dodana. Możesz teraz dodać do niej zdjęcia.")
        return reverse('panel_post_edit', args=[self.object.pk])


class PanelPostUpdateView(PanelBaseView, UpdateView):
    model = Post
    form_class = PanelPostForm
    template_name = 'panel/post_form.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['photo_form'] = PanelPostImageForm()
        ctx['photos'] = self.object.images.all()
        return ctx

    def get_success_url(self):
        messages.success(self.request, "Zmiany zapisane.")
        return reverse('panel_post_edit', args=[self.object.pk])


class PanelPostDeleteView(PanelBaseView, DeleteView):
    model = Post
    template_name = 'panel/confirm_delete.html'
    success_url = reverse_lazy('panel_post_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['back_url'] = reverse('panel_post_list')
        ctx['label'] = str(self.object)
        return ctx


@login_required
def panel_post_photo_add(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.method == 'POST':
        form = PanelPostImageForm(request.POST, request.FILES)
        if form.is_valid():
            photo = form.save(commit=False)
            photo.post = post
            photo.save()
            messages.success(request, "Zdjęcie dodane.")
        else:
            messages.error(request, "Nie udało się dodać zdjęcia — wybierz plik.")
    return redirect('panel_post_edit', pk=post.pk)


@login_required
def panel_post_photo_delete(request, pk):
    photo = get_object_or_404(PostImage, pk=pk)
    post_pk = photo.post_id
    if request.method == 'POST':
        photo.image.delete(save=False)
        photo.delete()
        messages.success(request, "Zdjęcie usunięte.")
    return redirect('panel_post_edit', pk=post_pk)


# ---------- Wydarzenia ----------

class PanelEventListView(PanelBaseView, ListView):
    model = Event
    template_name = 'panel/event_list.html'
    context_object_name = 'events'
    ordering = ['-start_date']


class PanelEventCreateView(PanelBaseView, CreateView):
    model = Event
    form_class = PanelEventForm
    template_name = 'panel/event_form.html'

    def form_valid(self, form):
        base = slugify(form.instance.title)[:200] or 'wydarzenie'
        slug = base
        i = 2
        while Event.objects.filter(slug=slug).exists():
            slug = f"{base}-{i}"
            i += 1
        form.instance.slug = slug
        return super().form_valid(form)

    def get_success_url(self):
        messages.success(self.request, "Wydarzenie dodane. Możesz teraz dodać do niego zdjęcia.")
        return reverse('panel_event_edit', args=[self.object.pk])


class PanelEventUpdateView(PanelBaseView, UpdateView):
    model = Event
    form_class = PanelEventForm
    template_name = 'panel/event_form.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['photo_form'] = PanelEventPhotoForm()
        ctx['photos'] = self.object.photos.all()
        return ctx

    def get_success_url(self):
        messages.success(self.request, "Zmiany zapisane.")
        return reverse('panel_event_edit', args=[self.object.pk])


class PanelEventDeleteView(PanelBaseView, DeleteView):
    model = Event
    template_name = 'panel/confirm_delete.html'
    success_url = reverse_lazy('panel_event_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['back_url'] = reverse('panel_event_list')
        ctx['label'] = str(self.object)
        return ctx


@login_required
def panel_event_photo_add(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if request.method == 'POST':
        form = PanelEventPhotoForm(request.POST, request.FILES)
        if form.is_valid():
            photo = form.save(commit=False)
            photo.event = event
            photo.save()
            messages.success(request, "Zdjęcie dodane.")
        else:
            messages.error(request, "Nie udało się dodać zdjęcia — wybierz plik.")
    return redirect('panel_event_edit', pk=event.pk)


@login_required
def panel_event_photo_delete(request, pk):
    photo = get_object_or_404(EventPhoto, pk=pk)
    event_pk = photo.event_id
    if request.method == 'POST':
        photo.image.delete(save=False)
        photo.delete()
        messages.success(request, "Zdjęcie usunięte.")
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


class PanelPersonDeleteView(PanelBaseView, DeleteView):
    model = Person
    template_name = 'panel/confirm_delete.html'
    success_url = reverse_lazy('panel_person_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['back_url'] = reverse('panel_person_list')
        ctx['label'] = str(self.object)
        return ctx


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


class PanelDocumentDeleteView(PanelBaseView, DeleteView):
    model = Document
    template_name = 'panel/confirm_delete.html'
    success_url = reverse_lazy('panel_document_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['back_url'] = reverse('panel_document_list')
        ctx['label'] = str(self.object)
        return ctx


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


class PanelHeroDeleteView(PanelBaseView, DeleteView):
    model = HeroImage
    template_name = 'panel/confirm_delete.html'
    success_url = reverse_lazy('panel_hero_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['back_url'] = reverse('panel_hero_list')
        ctx['label'] = str(self.object)
        return ctx
