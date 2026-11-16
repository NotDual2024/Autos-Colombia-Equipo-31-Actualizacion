"""Pantallas de entradas y salidas (HU-001 a HU-004; mockups M-02 a M-05)."""
from datetime import timedelta
from math import ceil
from urllib.parse import urlencode

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from apps.core import reloj
from apps.core.errores import ErrorNegocio
from apps.novedades import selectors as consultas_novedades
from apps.novedades.models import TipoNovedad
from apps.pagos import services as vigencia
from apps.usuarios_celdas.models import Categoria, TipoVehiculo
from apps.usuarios_celdas.selectors import normalizar_placa

from . import selectors, services
from .forms import FiltroHistorialForm
from .models import Estadia

CELDAS_POR_PAGINA = 24


def _estado_vehiculo(vehiculo):
    """Datos del vehículo para la tarjeta 'Datos del vehículo'."""
    pago = vigencia.ultimo_pago(vehiculo)
    return {
        "vehiculo": vehiculo,
        "ultimo_pago": pago,
        "vigente": vigencia.esta_vigente(vehiculo, reloj.hoy()),
        "cliente_activo": vehiculo.propietario.activo and vehiculo.activo,
    }


def _cuadricula(categoria, pagina, seleccionada=None):
    """Celdas de una categoría, en bloques de 24 (CHG-002, punto 4)."""
    celdas = selectors.celdas_de_categoria(categoria)
    total_paginas = max(ceil(len(celdas) / CELDAS_POR_PAGINA), 1)
    if pagina is None:
        if seleccionada:
            indice = next((i for i, c in enumerate(celdas) if c["codigo"] == seleccionada), 0)
        else:
            indice = next((i for i, c in enumerate(celdas) if not c["ocupada"]), 0)
        pagina = indice // CELDAS_POR_PAGINA + 1
    pagina = min(max(pagina, 1), total_paginas)
    inicio = (pagina - 1) * CELDAS_POR_PAGINA
    return {
        "celdas": celdas[inicio:inicio + CELDAS_POR_PAGINA],
        "pagina": pagina,
        "total_paginas": total_paginas,
        "disponibles": sum(1 for c in celdas if not c["ocupada"]),
        "total": len(celdas),
        "categoria": categoria,
        "categoria_nombre": Categoria(categoria).label,
        "prefijo": "Zona M" if categoria == Categoria.MOTO else "Zona A",
    }


def _entero(valor):
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


@login_required
@require_http_methods(["GET", "POST"])
def registrar_entrada(request):
    """HU-001 / UC-02 a UC-04."""
    placa = normalizar_placa(request.POST.get("placa") or request.GET.get("placa", ""))
    contexto = {"placa": placa, "error": None, "detalle_error": None, "exito": None}

    if request.method == "POST":
        try:
            estadia = services.registrar_entrada(placa, request.POST.get("celda", ""), request.user)
            return redirect(f"{reverse('entradas_salidas:entrada')}?{urlencode({'ok': estadia.pk})}")
        except ErrorNegocio as error:
            contexto["error"] = error.mensaje

    exito_id = _entero(request.GET.get("ok"))
    if exito_id:
        estadia = selectors.ESTADIAS.filter(pk=exito_id).first()
        if estadia:
            contexto.update(exito=estadia, placa=estadia.vehiculo.placa, **_estado_vehiculo(estadia.vehiculo))
            contexto["cuadricula"] = _cuadricula(estadia.vehiculo.categoria(), None, estadia.celda.codigo)
            contexto["seleccionada"] = estadia.celda.codigo
            return render(request, "entradas_salidas/entrada.html", contexto)

    if placa:
        try:
            vehiculo = services.obtener_vehiculo(placa)
        except ErrorNegocio as error:
            contexto["error"] = error.mensaje
            return render(request, "entradas_salidas/entrada.html", contexto)
        contexto.update(_estado_vehiculo(vehiculo))
        error_validacion = None
        try:
            services.validar_entrada(vehiculo)
        except ErrorNegocio as error:
            error_validacion = error.mensaje
        contexto["error"] = contexto["error"] or error_validacion
        if contexto["error"] == services.MSG_YA_DENTRO:
            abierta = selectors.estadia_abierta(vehiculo)
            if abierta:
                hora = timezone.localtime(abierta.fecha_hora_entrada)
                contexto["detalle_error"] = (
                    f"{vehiculo.placa} tiene una entrada abierta desde las {hora:%H:%M} y ocupa la celda "
                    f"{abierta.celda.codigo}. Registra su salida antes de un nuevo ingreso."
                )
        contexto["bloqueado"] = bool(error_validacion)
        seleccionada = request.POST.get("celda") if request.method == "POST" else None
        contexto["seleccionada"] = seleccionada
        contexto["cuadricula"] = _cuadricula(vehiculo.categoria(), _entero(request.GET.get("pagina")), seleccionada)
    return render(request, "entradas_salidas/entrada.html", contexto)


@login_required
@require_http_methods(["GET", "POST"])
def registrar_salida(request):
    """HU-002 / UC-05."""
    placa = normalizar_placa(request.POST.get("placa") or request.GET.get("placa", ""))
    contexto = {"placa": placa, "error": None, "tipos_novedad": TipoNovedad.choices}

    if request.method == "POST":
        try:
            estadia = services.registrar_salida(placa, request.user)
            return redirect(f"{reverse('entradas_salidas:salida')}?{urlencode({'ok': estadia.pk})}")
        except ErrorNegocio as error:
            contexto["error"] = error.mensaje

    exito_id = _entero(request.GET.get("ok"))
    estadia = None
    if exito_id:
        estadia = selectors.ESTADIAS.filter(pk=exito_id, fecha_hora_salida__isnull=False).first()
        contexto["exito"] = estadia
    elif placa and not contexto["error"]:
        try:
            estadia = services.buscar_estadia_abierta(placa)
        except ErrorNegocio as error:
            contexto["error"] = error.mensaje
    if estadia:
        contexto["estadia"] = estadia
        contexto["placa"] = estadia.vehiculo.placa
        contexto["novedades"] = consultas_novedades.de_estadia(estadia)
        contexto["vigente"] = vigencia.esta_vigente(estadia.vehiculo, reloj.hoy())
        contexto["ahora_local"] = reloj.ahora().strftime("%Y-%m-%dT%H:%M")
    return render(request, "entradas_salidas/salida.html", contexto)


@login_required
def vehiculos_dentro(request):
    """HU-003 / UC-06: ocupación, consulta de celda y lista paginada."""
    tipo = request.GET.get("tipo") or ""
    placa = normalizar_placa(request.GET.get("placa", ""))
    codigo_celda = (request.GET.get("celda") or "").strip().upper()
    estadias = selectors.vehiculos_dentro(tipo or None, placa or None)
    pagina = Paginator(estadias, 8).get_page(request.GET.get("pagina"))
    contexto = {
        "ocupacion": selectors.ocupacion_por_categoria(),
        "pagina": pagina,
        "total": estadias.count(),
        "tipo": tipo,
        "placa": placa,
        "tipos": TipoVehiculo.choices,
        "codigo_celda": codigo_celda,
        "parametros": urlencode({k: v for k, v in {"tipo": tipo, "placa": placa}.items() if v}),
    }
    if codigo_celda:
        celda, estadia = selectors.ocupacion_celda(codigo_celda)
        contexto["consulta_celda"] = {"celda": celda, "estadia": estadia}
    return render(request, "entradas_salidas/dentro.html", contexto)


@login_required
def historial(request):
    """HU-004 / UC-07."""
    hoy = reloj.hoy()
    datos = request.GET.copy()
    if "desde" not in datos and "hasta" not in datos:
        datos["desde"] = (hoy - timedelta(days=30)).isoformat()
        datos["hasta"] = hoy.isoformat()
    form = FiltroHistorialForm(datos)
    registros = Estadia.objects.none()
    if form.is_valid():
        registros = selectors.historial(
            normalizar_placa(form.cleaned_data.get("placa") or "") or None,
            form.cleaned_data.get("desde"), form.cleaned_data.get("hasta"),
        )
    pagina = Paginator(registros, 10).get_page(request.GET.get("pagina"))
    seleccion = None
    sel_id = _entero(request.GET.get("sel"))
    if sel_id:
        seleccion = selectors.ESTADIAS.filter(pk=sel_id).first()
    parametros = {k: datos.get(k) for k in ("placa", "desde", "hasta") if datos.get(k)}
    return render(request, "entradas_salidas/historial.html", {
        "form": form, "pagina": pagina, "total": registros.count() if form.is_valid() else 0,
        "seleccion": seleccion,
        "novedades_seleccion": consultas_novedades.de_estadia(seleccion) if seleccion else [],
        "parametros": urlencode(parametros),
    })
