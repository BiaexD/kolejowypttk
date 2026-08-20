from django.contrib import admin
from .models import Post, PostImage, Event, EventPhoto, Person, Document, HeroImage, CentralNews
from .forms import PostAdminForm


class EventPhotoInline(admin.TabularInline):
    model = EventPhoto
    extra = 3
    fields = ('image', 'caption', 'order')


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'start_date', 'location', 'is_published')
    list_filter = ('is_published', 'start_date')
    search_fields = ('title', 'description', 'location')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [EventPhotoInline]


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ("name", "body", "role", "order", "email", "phone")
    list_filter = ("body", "role")
    search_fields = ("name", "email", "phone")
    ordering = ("body", "order", "role", "name")


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'is_public', 'created')
    list_filter = ('is_public', 'category')
    search_fields = ('title', 'category')
    ordering = ('category', 'title')


class PostImageInline(admin.TabularInline):
    model = PostImage
    extra = 3
    fields = ('image', 'caption', 'order')

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    form = PostAdminForm
    list_display = ('title', 'published_at', 'is_published', 'source')
    list_filter = ('is_published', 'source')
    search_fields = ('title', 'body', 'fb_post_id', 'fb_perma')
    ordering = ('-published_at',)
    inlines = [PostImageInline]

    fieldsets = (
        ('Treść', {'fields': ('title', 'body', 'published_at', 'is_published')}),
        ('Stare zdjęcie / zgodność wsteczna', {'fields': ('image_url',)}),
        ('Źródła (opcjonalne)', {'fields': ('fb_perma', 'source')}),
    )
    exclude = ('fb_post_id',)


@admin.register(CentralNews)
class CentralNewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'published_at')
    search_fields = ('title', 'excerpt')
    ordering = ('-published_at',)


@admin.register(HeroImage)
class HeroImageAdmin(admin.ModelAdmin):
    list_display = ('title','order','is_active','created')
    list_editable = ('order','is_active')
    search_fields = ('title','image_url')
    ordering = ('order','created')
