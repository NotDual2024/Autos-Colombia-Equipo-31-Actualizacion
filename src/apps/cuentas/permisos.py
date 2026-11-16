"""Control de acceso por rol (RNF-002)."""
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def solo_administrador(vista):
    """Exige sesión iniciada y rol Administrador; si no, responde 403 (acceso denegado)."""

    @login_required
    @wraps(vista)
    def envoltura(request, *args, **kwargs):
        if not request.user.es_administrador():
            raise PermissionDenied("Acceso denegado")
        return vista(request, *args, **kwargs)

    return envoltura
