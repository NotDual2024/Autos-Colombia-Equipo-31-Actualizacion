from django.urls import path

from . import views

app_name = "pagos"

urlpatterns = [
    path("registrar/", views.registrar, name="registrar"),
    path("registrado/<int:pago_id>/", views.registrado, name="registrado"),
    path("vehiculo/<int:vehiculo_id>/", views.pagos_vehiculo, name="vehiculo"),
    path("propietario/<int:propietario_id>/", views.pagos_propietario, name="propietario"),
    path("factura/<int:numero>/", views.factura, name="factura"),
    path("corregir/<int:pago_id>/", views.corregir, name="corregir"),
    path("por-vencer/", views.por_vencer, name="por_vencer"),
    path("tarifas/", views.tarifas_vista, name="tarifas"),
    path("descuentos/", views.descuentos_vista, name="descuentos"),
    path("descuentos/<int:descuento_id>/estado/", views.descuento_estado, name="descuento_estado"),
    path("ingresos/", views.ingresos, name="ingresos"),
]
