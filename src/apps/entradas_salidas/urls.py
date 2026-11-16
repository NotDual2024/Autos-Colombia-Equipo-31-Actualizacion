from django.urls import path

from . import views

app_name = "entradas_salidas"

urlpatterns = [
    path("entrada/", views.registrar_entrada, name="entrada"),
    path("salida/", views.registrar_salida, name="salida"),
    path("dentro/", views.vehiculos_dentro, name="dentro"),
    path("historial/", views.historial, name="historial"),
]
