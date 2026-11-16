"""Bitácora completa (M-25 / HU-023). Solo administrador; el operador la ve en las fichas."""
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.shortcuts import render

from . import services
from .models import Accion


def _fecha(texto):
    try:
        return datetime.strptime(texto, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


@login_required
def bitacora(request):
    # Control de rol sin importar cuentas, para no crear un ciclo de dependencias (DM-08).
    if not getattr(request.user, "es_administrador", lambda: False)():
        raise PermissionDenied("Acceso denegado")
    from django.contrib.auth import get_user_model

    filtros = {k: request.GET.get(k, "") for k in ("usuario", "accion", "desde", "hasta")}
    usuario_id = int(filtros["usuario"]) if filtros["usuario"].isdigit() else None
    operaciones = services.buscar(usuario_id, filtros["accion"] or None, _fecha(filtros["desde"]), _fecha(filtros["hasta"]))
    pagina = Paginator(operaciones, 25).get_page(request.GET.get("pagina"))
    return render(request, "bitacora/bitacora.html", {
        "pagina": pagina, "operaciones": pagina.object_list, "filtros": filtros,
        "usuarios": get_user_model().objects.order_by("username"), "acciones": Accion.choices,
    })
