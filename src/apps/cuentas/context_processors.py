from apps.core import reloj

from . import turnos


def turno(request):
    """Texto del turno para el encabezado (RF-107): 'Turno 06:00 – 14:00'."""
    usuario = getattr(request, "user", None)
    if not usuario or not usuario.is_authenticated:
        return {}
    return {"texto_turno": turnos.texto_turno(usuario, reloj.ahora())}
