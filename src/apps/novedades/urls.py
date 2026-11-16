from django.urls import path

from . import views

app_name = "novedades"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("registrar/", views.registrar, name="registrar"),
]
