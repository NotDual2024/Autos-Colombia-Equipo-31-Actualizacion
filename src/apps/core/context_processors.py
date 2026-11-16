from django.conf import settings

from . import reloj


def contexto_general(request):
    """Datos comunes del encabezado: nombre del sistema y fecha y hora actuales."""
    return {"nombre_sistema": settings.NOMBRE_SISTEMA, "ahora": reloj.ahora()}
