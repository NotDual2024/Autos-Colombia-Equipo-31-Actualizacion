"""Pantallas de novedades (HU-005, HU-006; mockups M-06, M-07; referencia P4)."""
from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods

from apps.core import reloj
from apps.core.errores import ErrorNegocio
from apps.usuarios_celdas.selectors import normalizar_placa

from . import selectors, services
from .models import TipoNovedad


def _leer_fecha_hora(texto: str) -> datetime | None:
    try:
        return timezone.make_aware(datetime.fromisoformat(texto))
    except (TypeError, ValueError):
        return None


@login_required
@require_http_methods(["GET", "POST"])
def registrar(request):
    """HU-005 / UC-08. También recibe el modal de las pantallas de salida."""
    ahora_local = reloj.ahora().strftime("%Y-%m-%dT%H:%M")
    datos = {
        "placas": request.POST.get("placas") or normalizar_placa(request.GET.get("placa", "")),
        "tipo": request.POST.get("tipo", TipoNovedad.OBSERVACION),
        "ocurrencia": request.POST.get("ocurrencia", ahora_local),
        "descripcion": request.POST.get("descripcion", ""),
    }
    error = None
    if request.method == "POST":
        texto_placas = " ".join(
            p for p in [request.POST.get("placa_principal", ""), request.POST.get("otras_placas", ""), request.POST.get("placas", "")] if p
        )
        siguiente = request.POST.get("siguiente", "")
        ocurrencia = _leer_fecha_hora(request.POST.get("ocurrencia", ""))
        try:
            if ocurrencia is None:
                raise ErrorNegocio("Indica la fecha y hora del hecho.")
            novedad = services.registrar(
                services.separar_placas(texto_placas), request.POST.get("tipo", ""), ocurrencia,
                request.POST.get("descripcion", ""), request.user,
            )
            cantidad = novedad.vinculos.count()
            messages.success(request, f"Novedad {novedad.codigo} registrada y vinculada a {cantidad} vehículo{'s' if cantidad != 1 else ''}.")
            if siguiente and url_has_allowed_host_and_scheme(siguiente, {request.get_host()}):
                return redirect(siguiente)
            return redirect("novedades:lista")
        except ErrorNegocio as e:
            error = e.mensaje
            datos["placas"] = texto_placas
    return render(request, "novedades/registrar.html", {
        "datos": datos, "error": error, "tipos": TipoNovedad.choices, "ahora_local": ahora_local,
    })


@login_required
def lista(request):
    """HU-006 / UC-09."""
    placa = normalizar_placa(request.GET.get("placa", ""))
    tipo = request.GET.get("tipo", "")
    desde = _fecha(request.GET.get("desde"))
    hasta = _fecha(request.GET.get("hasta"))
    novedades = selectors.buscar(placa or None, tipo or None, desde, hasta)
    pagina = Paginator(novedades, 10).get_page(request.GET.get("pagina"))
    return render(request, "novedades/lista.html", {
        "pagina": pagina, "placa": placa, "tipo": tipo, "tipos": TipoNovedad.choices,
        "desde": request.GET.get("desde", ""), "hasta": request.GET.get("hasta", ""),
    })


def _fecha(texto):
    try:
        return datetime.strptime(texto, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None
