from django.urls import path

from . import panel_views as views

urlpatterns = [
    path('', views.panel_dashboard, name='panel_dashboard'),
    path('logowanie/', views.PanelLoginView.as_view(), name='panel_login'),
    path('wylogowanie/', views.PanelLogoutView.as_view(), name='panel_logout'),
    path('rejestracja/', views.panel_signup, name='panel_signup'),

    path('aktualnosci/', views.PanelPostListView.as_view(), name='panel_post_list'),
    path('aktualnosci/nowa/', views.PanelPostCreateView.as_view(), name='panel_post_create'),
    path('aktualnosci/kosz/', views.panel_post_trash, name='panel_post_trash'),
    path('aktualnosci/<int:pk>/', views.PanelPostUpdateView.as_view(), name='panel_post_edit'),
    path('aktualnosci/<int:pk>/usun/', views.PanelPostDeleteView.as_view(), name='panel_post_delete'),
    path('aktualnosci/<int:pk>/przywroc/', views.panel_post_restore, name='panel_post_restore'),
    path('aktualnosci/<int:pk>/usun-na-zawsze/', views.panel_post_purge, name='panel_post_purge'),
    path('aktualnosci/<int:pk>/zdjecie/dodaj/', views.panel_post_photo_add, name='panel_post_photo_add'),
    path('aktualnosci/zdjecie/<int:pk>/usun/', views.panel_post_photo_delete, name='panel_post_photo_delete'),
    path('aktualnosci/<int:pk>/dokument/dodaj/', views.panel_post_document_add, name='panel_post_document_add'),
    path('aktualnosci/dokument/<int:pk>/usun/', views.panel_post_document_delete, name='panel_post_document_delete'),

    path('wydarzenia/', views.panel_event_list, name='panel_event_list'),
    path('wydarzenia/nowe/', views.PanelEventCreateView.as_view(), name='panel_event_create'),
    path('wydarzenia/kosz/', views.panel_event_trash, name='panel_event_trash'),
    path('wydarzenia/<int:pk>/', views.PanelEventUpdateView.as_view(), name='panel_event_edit'),
    path('wydarzenia/<int:pk>/usun/', views.PanelEventDeleteView.as_view(), name='panel_event_delete'),
    path('wydarzenia/<int:pk>/przywroc/', views.panel_event_restore, name='panel_event_restore'),
    path('wydarzenia/<int:pk>/usun-na-zawsze/', views.panel_event_purge, name='panel_event_purge'),
    path('wydarzenia/<int:pk>/zdjecie/dodaj/', views.panel_event_photo_add, name='panel_event_photo_add'),
    path('wydarzenia/zdjecie/<int:pk>/usun/', views.panel_event_photo_delete, name='panel_event_photo_delete'),
    path('wydarzenia/<int:pk>/dokument/dodaj/', views.panel_event_document_add, name='panel_event_document_add'),
    path('wydarzenia/dokument/<int:pk>/usun/', views.panel_event_document_delete, name='panel_event_document_delete'),

    path('wladze/', views.PanelPersonListView.as_view(), name='panel_person_list'),
    path('wladze/nowa/', views.PanelPersonCreateView.as_view(), name='panel_person_create'),
    path('wladze/kosz/', views.panel_person_trash, name='panel_person_trash'),
    path('wladze/<int:pk>/', views.PanelPersonUpdateView.as_view(), name='panel_person_edit'),
    path('wladze/<int:pk>/usun/', views.PanelPersonDeleteView.as_view(), name='panel_person_delete'),
    path('wladze/<int:pk>/przywroc/', views.panel_person_restore, name='panel_person_restore'),
    path('wladze/<int:pk>/usun-na-zawsze/', views.panel_person_purge, name='panel_person_purge'),

    path('dokumenty/', views.PanelDocumentListView.as_view(), name='panel_document_list'),
    path('dokumenty/nowy/', views.PanelDocumentCreateView.as_view(), name='panel_document_create'),
    path('dokumenty/kosz/', views.panel_document_trash, name='panel_document_trash'),
    path('dokumenty/<int:pk>/', views.PanelDocumentUpdateView.as_view(), name='panel_document_edit'),
    path('dokumenty/<int:pk>/usun/', views.PanelDocumentDeleteView.as_view(), name='panel_document_delete'),
    path('dokumenty/<int:pk>/przywroc/', views.panel_document_restore, name='panel_document_restore'),
    path('dokumenty/<int:pk>/usun-na-zawsze/', views.panel_document_purge, name='panel_document_purge'),

    path('hero/', views.PanelHeroListView.as_view(), name='panel_hero_list'),
    path('hero/nowy/', views.PanelHeroCreateView.as_view(), name='panel_hero_create'),
    path('hero/kosz/', views.panel_hero_trash, name='panel_hero_trash'),
    path('hero/<int:pk>/', views.PanelHeroUpdateView.as_view(), name='panel_hero_edit'),
    path('hero/<int:pk>/usun/', views.PanelHeroDeleteView.as_view(), name='panel_hero_delete'),
    path('hero/<int:pk>/przywroc/', views.panel_hero_restore, name='panel_hero_restore'),
    path('hero/<int:pk>/usun-na-zawsze/', views.panel_hero_purge, name='panel_hero_purge'),
]
