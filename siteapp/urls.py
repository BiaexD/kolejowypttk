from django.urls import path
from django.contrib.sitemaps.views import sitemap
from . import views
from .sitemaps import StaticViewSitemap, NewsSitemap, EventSitemap

sitemaps = {
    "static": StaticViewSitemap,
    "aktualnosci": NewsSitemap,
    "wydarzenia": EventSitemap,
}

urlpatterns = [
    path('robots.txt', views.robots_txt, name='robots_txt'),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='sitemap'),
    path('', views.index, name='index'),
    path('aktualnosci/', views.news_list, name='news_list'),
    path('aktualnosci/<int:pk>/', views.news_detail, name='news_detail'),
    path('wydarzenia/', views.event_list, name='event_list'),
    path('wydarzenia/<slug:slug>/', views.event_detail, name='event_detail'),
    path('wladze/', views.board, name='board'),
    path('dokumenty/', views.docs_list, name='docs_list'),
    path('galeria/', views.gallery_albums, name='gallery_albums'),
    path('galeria/<str:album_id>/', views.gallery_album_detail, name='gallery_album_detail'),
    path('kontakt/', views.contact, name='contact'),
    path('historia/', views.historia, name='historia'),
    path('odznaki/', views.odznaki, name='odznaki'),

]
