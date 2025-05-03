from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_with_spotify, name='login'),
    path('callback/', views.spotify_callback, name='callback'),
    path('mood/', views.mood_selector, name='mood_selector'),
    path('add/', views.add_to_spotify, name='add_to_spotify'),

]