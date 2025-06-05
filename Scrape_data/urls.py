from django.urls import path
from . import views

urlpatterns = [
    path('', views.homePage, name="homePage_intership"),
    path('internship/', views.internship_view, name='live_internship'),
    path('download_csv/<str:filename>/', views.download_csv, name='download_csv'),
    # Add other paths here as necessary
]
