from django import forms
from .models import Post

class ContactForm(forms.Form):
    name = forms.CharField(max_length=120)
    email = forms.EmailField()
    message = forms.CharField(widget=forms.Textarea)
    honeypot = forms.CharField(required=False)

    def clean_honeypot(self):
        if self.cleaned_data.get('honeypot'):
            raise forms.ValidationError("Spam detected.")
        return ""

class PostAdminForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title','body','image_url','published_at','is_published','fb_perma', 'source']

    def clean(self):
        cleaned = super().clean()
        title = cleaned.get('title','').strip()
        body  = cleaned.get('body','').strip()

        if not title and not body:
            raise forms.ValidationError("Podaj przynajmniej tytuł lub treść.")
        return cleaned
