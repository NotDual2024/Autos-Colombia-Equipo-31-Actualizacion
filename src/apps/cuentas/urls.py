from django.urls import path

from . import views

app_name = "cuentas"

urlpatterns = [
    path("ingresar/", views.InicioSesionView.as_view(), name="login"),
    path("salir/", views.CierreSesionView.as_view(), name="logout"),
    path("operadores/", views.operadores, name="operadores"),
    path("operadores/<int:operador_id>/estado/", views.cambiar_estado, name="estado_operador"),
]
