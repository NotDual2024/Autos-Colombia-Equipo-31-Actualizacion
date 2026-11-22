from django.urls import path

from . import views

app_name = "usuarios_celdas"

urlpatterns = [
    path("propietarios/", views.propietarios, name="propietarios"),
    path("propietarios/nuevo/", views.propietario_form, name="propietario_nuevo"),
    path("propietarios/<int:propietario_id>/", views.propietario_ficha, name="propietario"),
    path("propietarios/<int:propietario_id>/editar/", views.propietario_form, name="propietario_editar"),
    path("propietarios/<int:propietario_id>/estado/", views.propietario_estado, name="propietario_estado"),
    path("vehiculos/", views.vehiculos, name="vehiculos"),
    path("vehiculos/nuevo/", views.vehiculo_form, name="vehiculo_nuevo"),
    path("vehiculos/<int:vehiculo_id>/", views.vehiculo_ficha, name="vehiculo"),
    path("vehiculos/<int:vehiculo_id>/editar/", views.vehiculo_form, name="vehiculo_editar"),
    path("vehiculos/<int:vehiculo_id>/estado/", views.vehiculo_estado, name="vehiculo_estado"),
    path("vehiculos/<int:vehiculo_id>/cambio-propietario/", views.solicitar_cambio, name="solicitar_cambio"),
    path("solicitudes/", views.solicitudes, name="solicitudes"),
    path("solicitudes/<int:solicitud_id>/resolver/", views.resolver_solicitud, name="resolver_solicitud"),
    path("celdas/", views.mapa_celdas, name="mapa"),
    path("celdas/administrar/", views.celdas, name="celdas"),
    path("celdas/<int:celda_id>/tipo/", views.celda_tipo, name="celda_tipo"),
    path("celdas/<int:celda_id>/estado/", views.celda_estado, name="celda_estado"),
    path("celdas/<int:celda_id>/eliminar/", views.celda_eliminar, name="celda_eliminar"),
]
