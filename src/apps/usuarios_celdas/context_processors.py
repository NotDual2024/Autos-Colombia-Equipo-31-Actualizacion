from . import selectors


def solicitudes(request):
    """Número de solicitudes pendientes para el menú del administrador."""
    usuario = getattr(request, "user", None)
    if usuario and usuario.is_authenticated and usuario.es_administrador():
        return {"solicitudes_pendientes": selectors.pendientes()}
    return {}
