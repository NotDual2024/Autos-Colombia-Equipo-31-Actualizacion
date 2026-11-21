"""Pantallas de pagos (M-26 a M-35): registrar, vigencia e historial, factura, corrección, tarifas,
descuentos, por vencer e ingresos."""
from datetime import date

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from apps.core import reloj
from apps.core.errores import ErrorNegocio
from apps.cuentas.permisos import solo_administrador
from apps.usuarios_celdas.models import Categoria, Propietario, Vehiculo
from apps.usuarios_celdas.selectors import normalizar_placa

from . import registro, selectors, services as vigencia, tarifas
from .models import Descuento, MedioPago, Pago

CLAVE_RESULTADO = "resultado_pago"


def _contexto_formulario(vehiculo: Vehiculo | None, datos: dict) -> dict:
    contexto = {"medios": MedioPago.choices, "descuentos": tarifas.habilitados(), "datos": datos, "vehiculo": vehiculo,
                "meses_opciones": range(1, registro.MESES_MAXIMO + 1)}
    if vehiculo is not None:
        estado = vigencia.estado(vehiculo, reloj.hoy())
        contexto["estado"] = estado
        if not datos.get("meses"):
            datos["meses"] = str(max(1, estado.meses_pendientes))
        try:
            contexto["resumen"] = registro.preparar(vehiculo, datos.get("meses"), datos.get("descuento"))
        except ErrorNegocio as e:
            contexto["error"] = e.mensaje
    return contexto


@login_required
@require_http_methods(["GET", "POST"])
def registrar(request):
    """M-26 / HU-024: buscar la placa, ver el resumen calculado y confirmar."""
    fuente = request.POST if request.method == "POST" else request.GET
    datos = {c: fuente.get(c, "") for c in ("placa", "meses", "medio", "descuento")}
    datos["placa"] = normalizar_placa(datos["placa"]) if datos["placa"] else ""
    vehiculo = Vehiculo.objects.select_related("propietario").filter(placa=datos["placa"]).first() if datos["placa"] else None
    error = None
    if datos["placa"] and vehiculo is None:
        error = f"No hay un vehículo registrado con la placa {datos['placa']}."
    if request.method == "POST" and vehiculo is not None:
        try:
            resultado = registro.registrar(vehiculo, datos["meses"], datos["medio"], datos["descuento"], request.user)
            request.session[CLAVE_RESULTADO] = {"pago": resultado.pago.pk, "correo": resultado.correo_enviado,
                                                "reactivados": resultado.reactivados, "advertencias": resultado.advertencias}
            return redirect("pagos:registrado", pago_id=resultado.pago.pk)
        except ErrorNegocio as e:
            error = e.mensaje
    contexto = _contexto_formulario(vehiculo, datos)
    contexto["error"] = error or contexto.get("error")
    return render(request, "pagos/registrar.html", contexto)


@login_required
def registrado(request, pago_id: int):
    """M-27 / HU-024, HU-028: resultado del pago, con reactivaciones y advertencias."""
    pago = get_object_or_404(Pago.objects.select_related("vehiculo__propietario", "registrado_por"), pk=pago_id)
    datos = request.session.pop(CLAVE_RESULTADO, None)
    if not datos or datos.get("pago") != pago.pk:
        datos = {"correo": pago.correos_confirmacion.filter(resultado="ENVIADO_SIMULADO").exists(),
                 "reactivados": [], "advertencias": []}
    datos.pop("pago", None)
    return render(request, "pagos/registrado.html", {
        **datos, "pago": pago, "estado": vigencia.estado(pago.vehiculo, reloj.hoy()),
    })


@login_required
def pagos_vehiculo(request, vehiculo_id: int):
    """M-29 / HU-025, HU-026."""
    vehiculo = get_object_or_404(Vehiculo.objects.select_related("propietario"), pk=vehiculo_id)
    pagos = list(selectors.historial_vehiculo(vehiculo))
    return render(request, "pagos/historial.html", {
        "vehiculo": vehiculo, "estado": vigencia.estado(vehiculo, reloj.hoy()), "pagos": pagos,
        "corregibles": _corregibles(pagos, request.user), "titulo": f"Pagos de {vehiculo.placa}",
    })


@login_required
def pagos_propietario(request, propietario_id: int):
    """M-29 / HU-026: pagos de todos los vehículos del propietario."""
    propietario = get_object_or_404(Propietario, pk=propietario_id)
    pagos = list(selectors.historial_propietario(propietario))
    estados = [(v, vigencia.estado(v, reloj.hoy())) for v in propietario.vehiculos.order_by("placa")]
    return render(request, "pagos/historial.html", {
        "propietario": propietario, "estados": estados, "pagos": pagos,
        "corregibles": _corregibles(pagos, request.user), "titulo": f"Pagos de {propietario.nombre_completo}",
    })


def _corregibles(pagos: list[Pago], usuario) -> set[int]:
    """Pagos que el usuario puede corregir ahora: el último registrado de cada vehículo, dentro de su ventana (RN-44)."""
    ahora = reloj.ahora()
    ultimos = {}
    for p in pagos:
        if not p.esta_corregido:
            actual = ultimos.get(p.vehiculo_id)
            if actual is None or (p.periodo_fin, p.pk) > (actual.periodo_fin, actual.pk):
                ultimos[p.vehiculo_id] = p
    return {p.pk for p in ultimos.values() if p.corregible_por(usuario, ahora)}


@login_required
def factura(request, numero: int):
    """M-28 / HU-026, HU-029: página para imprimir (el navegador la guarda como PDF)."""
    pago = selectors.factura(numero)
    if pago is None:
        return render(request, "pagos/factura_no_existe.html", {"numero": numero}, status=404)
    reemplazo = getattr(pago, "reemplazo", None)
    return render(request, "pagos/factura.html", {
        "pago": pago, "reemplazo": reemplazo, "parqueadero": settings.DATOS_FACTURA,
    })


@login_required
@require_http_methods(["GET", "POST"])
def corregir(request, pago_id: int):
    """M-30 / HU-029."""
    pago = get_object_or_404(Pago.objects.select_related("vehiculo__propietario", "registrado_por", "descuento"), pk=pago_id)
    fuente = request.POST if request.method == "POST" else request.GET
    datos = {"meses": fuente.get("meses", str(pago.meses)), "medio": fuente.get("medio", pago.medio),
             "descuento": fuente.get("descuento", str(pago.descuento_id or "")), "motivo": fuente.get("motivo", "")}
    error = None
    if pago.esta_corregido:
        error = "Este pago ya fue corregido; corrige el pago que lo reemplazó."
    elif not pago.corregible_por(request.user, reloj.ahora()):
        error = "Este pago solo lo puede corregir el administrador"
    elif not registro.es_ultimo(pago):
        error = "Solo se puede corregir el último pago registrado del vehículo. Corrige primero los posteriores."
    puede = error is None
    if request.method == "POST" and puede:
        try:
            resultado = registro.corregir(pago.pk, datos["motivo"], datos["meses"], datos["medio"], datos["descuento"], request.user)
            request.session[CLAVE_RESULTADO] = {"pago": resultado.pago.pk, "correo": resultado.correo_enviado,
                                                "reactivados": resultado.reactivados, "advertencias": resultado.advertencias,
                                                "corrigio": pago.numero_factura_texto}
            return redirect("pagos:registrado", pago_id=resultado.pago.pk)
        except ErrorNegocio as e:
            error = e.mensaje
    resumen = None
    if puede:
        try:
            resumen = registro.preparar(pago.vehiculo, datos["meses"], datos["descuento"], corrige=pago)
        except ErrorNegocio as e:
            error = e.mensaje
    descuentos = list(tarifas.habilitados())
    if pago.descuento and pago.descuento not in descuentos:
        descuentos.append(pago.descuento)
    return render(request, "pagos/corregir.html", {
        "pago": pago, "datos": datos, "resumen": resumen, "error": error, "puede": puede,
        "medios": MedioPago.choices, "descuentos": descuentos, "meses_opciones": range(1, registro.MESES_MAXIMO + 1),
        "minutos": int((reloj.ahora() - pago.fecha_pago).total_seconds() // 60),
    })


@login_required
def por_vencer(request):
    """M-34 / HU-030."""
    return render(request, "pagos/por_vencer.html", {"filas": selectors.por_vencer(reloj.hoy()), "dias": selectors.DIAS_POR_VENCER})


# ------------------------------------------------------------------ administración
@solo_administrador
@require_http_methods(["GET", "POST"])
def tarifas_vista(request):
    """M-31 / HU-027."""
    datos = {"categoria": request.POST.get("categoria", Categoria.CARRO_CAMIONETA), "valor": request.POST.get("valor", ""),
             "vigente_desde": request.POST.get("vigente_desde", "")}
    error = None
    if request.method == "POST":
        try:
            desde = date.fromisoformat(datos["vigente_desde"]) if datos["vigente_desde"] else None
        except ValueError:
            desde = None
        try:
            tarifa = tarifas.registrar_tarifa(request.user, datos["categoria"], datos["valor"], desde)
            messages.success(request, f"Tarifa registrada: {tarifa.get_categoria_display()} {registro.pesos(tarifa.valor)} "
                                      f"desde {tarifa.vigente_desde:%d/%m/%Y}.")
            return redirect("pagos:tarifas")
        except ErrorNegocio as e:
            error = e.mensaje
    hoy = reloj.hoy()
    actuales = {t.pk for t in tarifas.actuales(hoy)}
    return render(request, "pagos/tarifas.html", {
        "actuales": tarifas.actuales(hoy), "historial": tarifas.historial(), "ids_actuales": actuales, "hoy": hoy,
        "categorias": Categoria.choices, "datos": datos, "error": error,
    })


@solo_administrador
@require_http_methods(["GET", "POST"])
def descuentos_vista(request):
    """M-32 / HU-031."""
    datos = {"descripcion": request.POST.get("descripcion", ""), "porcentaje": request.POST.get("porcentaje", "")}
    error = None
    if request.method == "POST":
        try:
            d = tarifas.crear_descuento(request.user, datos["descripcion"], datos["porcentaje"])
            messages.success(request, f"Descuento creado y habilitado: {d}.")
            return redirect("pagos:descuentos")
        except ErrorNegocio as e:
            error = e.mensaje
    return render(request, "pagos/descuentos.html", {
        "descuentos": Descuento.objects.select_related("creado_por"), "datos": datos, "error": error,
    })


@solo_administrador
@require_POST
def descuento_estado(request, descuento_id: int):
    descuento = get_object_or_404(Descuento, pk=descuento_id)
    habilitar = request.POST.get("habilitado") == "1"
    tarifas.cambiar_estado_descuento(request.user, descuento, habilitar)
    messages.success(request, f"Descuento {'habilitado' if habilitar else 'deshabilitado'}: {descuento}.")
    return redirect("pagos:descuentos")


@solo_administrador
def ingresos(request):
    """M-35 / HU-032."""
    hoy = reloj.hoy()
    try:
        anio, mes = (int(x) for x in request.GET.get("mes", f"{hoy:%Y-%m}").split("-"))
        date(anio, mes, 1)
    except ValueError:
        anio, mes = hoy.year, hoy.month
    return render(request, "pagos/ingresos.html", {"informe": selectors.ingresos(anio, mes), "mes_valor": f"{anio:04d}-{mes:02d}"})
