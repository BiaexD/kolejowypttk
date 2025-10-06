from django.contrib import admin
from .models import Post, Event, Person, Document, FbAlbum, FbPhoto, HeroImage
from .forms import PostAdminForm


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'start_date', 'location', 'is_published')
    list_filter = ('is_published', 'start_date')
    search_fields = ('title', 'description', 'location')
    prepopulated_fields = {'slug': ('title',)}

@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ('name', 'role', 'order')
    list_editable = ('order',)
    list_filter = ('role',)
    search_fields = ('name',)

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'is_public', 'created')
    list_filter = ('is_public', 'category')
    search_fields = ('title', 'category')
    ordering = ('category', 'title')

@admin.register(FbAlbum)
class FbAlbumAdmin(admin.ModelAdmin):
    list_display = ('name', 'fb_album_id', 'count', 'updated')
    search_fields = ('name', 'fb_album_id')
    ordering = ('-updated',)

@admin.register(FbPhoto)
class FbPhotoAdmin(admin.ModelAdmin):
    list_display = ('fb_photo_id', 'album', 'created_time')
    search_fields = ('fb_photo_id', 'caption')
    list_filter = ('album',)
    ordering = ('-created_time',)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    form = PostAdminForm
    list_display = ('title','published_at','is_published','source')
    list_filter  = ('is_published','source')
    search_fields = ('title','body','fb_post_id','fb_perma')
    ordering = ('-published_at',)

    fieldsets = (
        ('Treść', {'fields': ('title','body','image_url','published_at','is_published')}),
        ('Źródła (opcjonalne)', {'fields': ('fb_perma','source')}),
    )
    exclude = ('fb_post_id',)


@admin.register(HeroImage)
class HeroImageAdmin(admin.ModelAdmin):
    list_display = ('title','order','is_active','created')
    list_editable = ('order','is_active')
    search_fields = ('title','image_url')
    ordering = ('order','created')
