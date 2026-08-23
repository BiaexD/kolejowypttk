from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm

from .models import Post, Event, Person, Document, HeroImage

User = get_user_model()


class PanelSignupForm(forms.Form):
    full_name = forms.CharField(label="Imię i nazwisko", max_length=150)
    email = forms.EmailField(label="Email")
    username = forms.CharField(label="Nazwa użytkownika (login)", max_length=150)
    password1 = forms.CharField(label="Hasło", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Powtórz hasło", widget=forms.PasswordInput)
    honeypot = forms.CharField(required=False, widget=forms.HiddenInput)

    def clean_honeypot(self):
        if self.cleaned_data.get('honeypot'):
            raise forms.ValidationError("Spam detected.")
        return ""

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Ta nazwa użytkownika jest już zajęta.")
        return username

    def clean(self):
        cleaned = super().clean()
        p1, p2 = cleaned.get('password1'), cleaned.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Hasła nie są takie same.")
        if p1 and len(p1) < 8:
            raise forms.ValidationError("Hasło musi mieć co najmniej 8 znaków.")
        return cleaned

    def save(self):
        data = self.cleaned_data
        full_name = data['full_name'].strip()
        first_name, _, last_name = full_name.partition(' ')
        user = User.objects.create_user(
            username=data['username'],
            email=data['email'],
            password=data['password1'],
            first_name=first_name,
            last_name=last_name,
            is_active=False,
        )
        return user


class PanelLoginForm(AuthenticationForm):
    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        if username and password:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                user = None
            if user and not user.is_active and user.check_password(password):
                raise forms.ValidationError(
                    "Twoje konto czeka jeszcze na zatwierdzenie przez administratora. "
                    "Spróbuj zalogować się ponownie później.",
                    code='inactive',
                )
        return super().clean()


class PanelPostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'body', 'published_at']
        widgets = {
            'published_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'body': forms.Textarea(attrs={'rows': 8}),
        }


class PanelEventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'description', 'start_date', 'end_date', 'location']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'end_date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'description': forms.Textarea(attrs={'rows': 8}),
        }


class PanelPersonForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = ['body', 'role', 'name', 'email', 'phone', 'order']


class PanelDocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['title', 'category', 'file']

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get('file') and not (self.instance and self.instance.file_url):
            raise forms.ValidationError("Wgraj plik dokumentu.")
        return cleaned


class PanelHeroImageForm(forms.ModelForm):
    class Meta:
        model = HeroImage
        fields = ['image', 'title', 'order']
