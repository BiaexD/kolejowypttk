from django.contrib import admin
from .models import Post, PostImage, Event, EventPhoto, Person, Document, HeroImage, CentralNews
from .forms import PostAdminForm, DocumentAdminForm

admin.site.site_header = "Panel administracyjny — PTTK Pracownicy Kolejowi"
admin.site.site_title = "PTTK Kolejowy — panel"
admin.site.index_title = "Zarządzanie treścią strony"


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
    form = DocumentAdminForm
    list_display = ('title', 'category', 'is_public', 'created')
    list_filter = ('is_public', 'category')
    search_fields = ('title', 'category')
    ordering = ('category', 'title')
    fieldsets = (
        (None, {'fields': ('title', 'category', 'file', 'is_public')}),
        ('Zaawansowane', {'fields': ('file_url',), 'classes': ('collapse',)}),
    )


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
        ('Zaawansowane', {'fields': ('image_url', 'fb_perma', 'source'), 'classes': ('collapse',)}),
    )
    exclude = ('fb_post_id',)


@admin.register(CentralNews)
class CentralNewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'published_at')
    search_fields = ('title', 'excerpt')
    ordering = ('-published_at',)

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(HeroImage)
class HeroImageAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', 'is_active', 'created')
    list_editable = ('order', 'is_active')
    search_fields = ('title', 'image_url')
    ordering = ('order', 'created')
    fieldsets = (
        (None, {'fields': ('image', 'title', 'is_active', 'order')}),
        ('Zaawansowane', {'fields': ('image_url',), 'classes': ('collapse',)}),
    )
