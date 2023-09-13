from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('album/<str:album_id>/', views.album, name='album'),
    path('artist/<str:artist_id>/', views.artist, name='artist'),
    path('track/<str:track_id>/', views.track, name='track'),
    path('analysis/', views.analysis, name='analysis'),
]
