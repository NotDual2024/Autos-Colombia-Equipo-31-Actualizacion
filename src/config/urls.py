"""URLs raíz. No se registra /admin (DEC-011)."""
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="entradas_salidas:entrada", permanent=False)),
    path("cuentas/", include("apps.cuentas.urls")),
    path("operacion/", include("apps.entradas_salidas.urls")),
    path("novedades/", include("apps.novedades.urls")),
    path("vencidos/", include("apps.notificaciones.urls")),
    path("clientes/", include("apps.usuarios_celdas.urls")),
    path("bitacora/", include("apps.bitacora.urls")),
]

handler403 = "apps.cuentas.views.acceso_denegado"
