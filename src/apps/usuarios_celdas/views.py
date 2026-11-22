"""Pantallas de propietarios, vehículos, cambio de propietario y mapa de celdas (M-13 a M-20)."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods, require_POST

from apps.bitacora import services as bitacora
from apps.bitacora.models import Accion, Entidad
from apps.core.errores import ErrorNegocio
from apps.cuentas.permisos import solo_administrador

from . import celdas as servicio_celdas, selectors, services
from .models import Categoria, Celda, EstadoSolicitud, MotivoInactivacion, Propietario, TipoVehiculo, Vehiculo


def _entero(valor, defecto=1):
    try:
        return int(valor)
    except (TypeError, ValueError):
        return defecto


# ------------------------------------------------------------------ propietarios
@login_required
def propietarios(request):
    """M-13 / HU-014."""
    texto = request.GET.get("q", "")
    pagina = Paginator(selectors.buscar_propietarios(texto), 12).get_page(request.GET.get("pagina"))
    return render(request, "usuarios_celdas/propietarios.html", {"pagina": pagina, "q": texto})


@login_required
@require_http_methods(["GET", "POST"])
def propietario_form(request, propietario_id: int | None = None):
    """M-14 / HU-012 y HU-015."""
    propietario = get_object_or_404(Propietario, pk=propietario_id) if propietario_id else None
    datos = {c: getattr(propietario, c) for c in services.CAMPOS_PROPIETARIO} if propietario else {}
    error = None
    if request.method == "POST":
        datos = {c: request.POST.get(c, "") for c in services.CAMPOS_PROPIETARIO}
        try:
            if propietario:
                services.modificar_propietario(propietario, datos, request.user)
                messages.success(request, "Propietario actualizado.")
            else:
                propietario = services.registrar_propietario(datos, request.user)
                messages.success(request, f"Propietario {propietario.nombre_completo} registrado.")
            return redirect("usuarios_celdas:propietario", propietario_id=propietario.pk)
        except ErrorNegocio as e:
            error = e.mensaje
    return render(request, "usuarios_celdas/propietario_form.html", {"propietario": propietario, "datos": datos, "error": error})


@login_required
def propietario_ficha(request, propietario_id: int):
    """M-15 / HU-014."""
    propietario = get_object_or_404(Propietario, pk=propietario_id)
    vehiculos = [{"vehiculo": v, "ubicacion": selectors.ubicacion(v)} for v in propietario.vehiculos.order_by("placa")]
    return render(request, "usuarios_celdas/propietario_ficha.html", {
        "propietario": propietario, "vehiculos": vehiculos,
        "operaciones": bitacora.de_entidad(Entidad.PROPIETARIO, propietario.pk)[:30],
        "motivos": MotivoInactivacion.choices,
        "inactivacion": bitacora.de_entidad(Entidad.PROPIETARIO, propietario.pk).filter(accion=Accion.INACTIVAR).first(),
    })


@login_required
@require_POST
def propietario_estado(request, propietario_id: int):
    propietario = get_object_or_404(Propietario, pk=propietario_id)
    activo = request.POST.get("activo") == "1"
    try:
        services.cambiar_estado_propietario(propietario, activo, request.user, request.POST.get("motivo"),
                                            request.POST.get("descripcion"))
        messages.success(request, f"Propietario {'activado' if activo else 'inactivado'}.")
    except ErrorNegocio as e:
        messages.error(request, e.mensaje)
    return redirect("usuarios_celdas:propietario", propietario_id=propietario.pk)


# ------------------------------------------------------------------ vehículos
@login_required
def vehiculos(request):
    texto, tipo = request.GET.get("q", ""), request.GET.get("tipo", "")
    pagina = Paginator(selectors.buscar_vehiculos(texto, tipo), 12).get_page(request.GET.get("pagina"))
    return render(request, "usuarios_celdas/vehiculos.html", {"pagina": pagina, "q": texto, "tipo": tipo, "tipos": TipoVehiculo.choices})


@login_required
@require_http_methods(["GET", "POST"])
def vehiculo_form(request, vehiculo_id: int | None = None):
    """M-16 / HU-013 y HU-015."""
    vehiculo = get_object_or_404(Vehiculo, pk=vehiculo_id) if vehiculo_id else None
    datos = {c: getattr(vehiculo, c) for c in services.CAMPOS_VEHICULO} if vehiculo else {"tipo": TipoVehiculo.CARRO}
    documento = request.POST.get("documento") or request.GET.get("documento", "")
    propietario = vehiculo.propietario if vehiculo else selectors.propietario_por_documento(documento)
    placa = request.POST.get("placa", "")
    error = None
    if request.method == "POST":
        datos = {c: request.POST.get(c, "") for c in services.CAMPOS_VEHICULO}
        try:
            if vehiculo:
                services.modificar_vehiculo(vehiculo, datos, request.user)
                messages.success(request, "Vehículo actualizado.")
            else:
                if propietario is None:
                    raise ErrorNegocio("Busca un propietario registrado por su cédula.")
                vehiculo = services.registrar_vehiculo(placa, datos, propietario, request.user)
                messages.success(request, f"Vehículo {vehiculo.placa} registrado.")
            return redirect("usuarios_celdas:vehiculo", vehiculo_id=vehiculo.pk)
        except ErrorNegocio as e:
            error = e.mensaje
    return render(request, "usuarios_celdas/vehiculo_form.html", {
        "vehiculo": vehiculo, "datos": datos, "placa": placa, "documento": documento,
        "propietario": propietario, "tipos": TipoVehiculo.choices, "error": error,
        "busco": bool(documento) and propietario is None,
    })


@login_required
def vehiculo_ficha(request, vehiculo_id: int):
    """M-17 / HU-014."""
    vehiculo = get_object_or_404(Vehiculo.objects.select_related("propietario"), pk=vehiculo_id)
    return render(request, "usuarios_celdas/vehiculo_ficha.html", {
        "vehiculo": vehiculo, "ubicacion": selectors.ubicacion(vehiculo),
        "historial": vehiculo.historial_propiedad.select_related("propietario"),
        "pendiente": vehiculo.solicitudes_cambio.filter(estado=EstadoSolicitud.PENDIENTE).select_related("propietario_nuevo").first(),
        "operaciones": bitacora.de_entidad(Entidad.VEHICULO, vehiculo.pk)[:30],
        "motivos": MotivoInactivacion.choices,
        "inactivacion": bitacora.de_entidad(Entidad.VEHICULO, vehiculo.pk).filter(accion=Accion.INACTIVAR).first(),
    })


@login_required
@require_POST
def vehiculo_estado(request, vehiculo_id: int):
    vehiculo = get_object_or_404(Vehiculo, pk=vehiculo_id)
    activo = request.POST.get("activo") == "1"
    try:
        services.cambiar_estado_vehiculo(vehiculo, activo, request.user, request.POST.get("motivo"),
                                         request.POST.get("descripcion"))
        messages.success(request, f"Vehículo {'activado' if activo else 'inactivado'}.")
    except ErrorNegocio as e:
        messages.error(request, e.mensaje)
    return redirect("usuarios_celdas:vehiculo", vehiculo_id=vehiculo.pk)


# ------------------------------------------------------------------ cambio de propietario
@login_required
@require_http_methods(["GET", "POST"])
def solicitar_cambio(request, vehiculo_id: int):
    """M-18 / HU-016."""
    vehiculo = get_object_or_404(Vehiculo.objects.select_related("propietario"), pk=vehiculo_id)
    documento = request.POST.get("documento") or request.GET.get("documento", "")
    nuevo = selectors.propietario_por_documento(documento)
    motivo = request.POST.get("motivo", "")
    error = None
    if request.method == "POST":
        try:
            if nuevo is None:
                raise ErrorNegocio("Busca al nuevo propietario por su cédula; debe estar registrado.")
            services.solicitar_cambio(vehiculo, nuevo, motivo, request.user)
            messages.success(request, "Solicitud enviada. Queda pendiente hasta que el administrador la resuelva.")
            return redirect("usuarios_celdas:vehiculo", vehiculo_id=vehiculo.pk)
        except ErrorNegocio as e:
            error = e.mensaje
    return render(request, "usuarios_celdas/solicitar_cambio.html", {
        "vehiculo": vehiculo, "documento": documento, "nuevo": nuevo, "motivo": motivo, "error": error,
        "busco": bool(documento) and nuevo is None,
    })


@solo_administrador
def solicitudes(request):
    """M-19 / HU-017."""
    estado = request.GET.get("estado", EstadoSolicitud.PENDIENTE)
    return render(request, "usuarios_celdas/solicitudes.html", {
        "solicitudes": selectors.solicitudes(estado), "estado": estado, "estados": EstadoSolicitud.choices,
    })


@solo_administrador
@require_POST
def resolver_solicitud(request, solicitud_id: int):
    try:
        if request.POST.get("decision") == "aprobar":
            vehiculo = services.aprobar_cambio(solicitud_id, request.user, request.POST.get("observacion", ""))
            messages.success(request, f"Cambio aprobado: {vehiculo.placa} ahora es de {vehiculo.propietario.nombre_completo}.")
        else:
            services.rechazar_cambio(solicitud_id, request.user, request.POST.get("observacion", ""))
            messages.success(request, "Solicitud rechazada.")
    except ErrorNegocio as e:
        messages.error(request, e.mensaje)
    return redirect("usuarios_celdas:solicitudes")


# ------------------------------------------------------------------ mapa de celdas
@login_required
def mapa_celdas(request):
    """M-20 / HU-018."""
    zona = request.GET.get("zona", "A")
    return render(request, "usuarios_celdas/mapa.html", {
        "mapa": selectors.mapa_celdas(zona, _entero(request.GET.get("bloque"))),
        "resumen": {z: selectors.mapa_celdas(z, 1) for z in ("A", "M")},
    })


# ------------------------------------------------------------------ gestión de celdas (CHG-003)
@solo_administrador
@require_http_methods(["GET", "POST"])
def celdas(request):
    """M-36 / HU-033, HU-034: lista de celdas con filtros y formulario para crear."""
    tipo_nuevo = request.POST.get("tipo") or request.GET.get("tipo_nuevo") or Categoria.CARRO_CAMIONETA
    datos = {"tipo": tipo_nuevo, "codigo": request.POST.get("codigo", "")}
    error = None
    if request.method == "POST":
        try:
            celda = servicio_celdas.crear(request.user, datos["tipo"], datos["codigo"])
            messages.success(request, f"Celda {celda.codigo} creada.")
            return redirect(f"{request.path}?q={celda.codigo}")
        except ErrorNegocio as e:
            error = e.mensaje
    filtros = {"tipo": request.GET.get("tipo", ""), "estado": request.GET.get("estado", ""), "q": request.GET.get("q", "")}
    filas = servicio_celdas.listar(filtros["tipo"], filtros["estado"], filtros["q"])
    pagina = Paginator(filas, 25).get_page(request.GET.get("pagina"))
    sugeridos = {t: servicio_celdas.siguiente_codigo(t) for t in Categoria.values}
    consulta = request.GET.copy()
    consulta.pop("pagina", None)
    return render(request, "usuarios_celdas/celdas.html", {
        "pagina": pagina, "filtros": filtros, "datos": datos, "error": error, "tipos": Categoria.choices,
        "sugeridos": sugeridos, "consulta": consulta.urlencode(), "total": len(filas),
        "estados": [(servicio_celdas.LIBRE, "Libre"), (servicio_celdas.OCUPADA, "Ocupada"), (servicio_celdas.INACTIVA, "Inactiva")],
    })


def _accion_celda(request, celda_id: int, accion):
    celda = get_object_or_404(Celda, pk=celda_id)
    try:
        mensaje = accion(celda)
        messages.success(request, mensaje)
    except ErrorNegocio as e:
        messages.error(request, f"{celda.codigo}: {e.mensaje}")
    volver = request.POST.get("volver", "")
    if not url_has_allowed_host_and_scheme(volver, allowed_hosts={request.get_host()}):
        volver = "usuarios_celdas:celdas"
    return redirect(volver or "usuarios_celdas:celdas")


@solo_administrador
@require_POST
def celda_tipo(request, celda_id: int):
    """HU-034: cambiar el tipo de una celda libre que nunca se usó."""
    def accion(celda):
        anterior = celda.codigo
        celda = servicio_celdas.cambiar_tipo(request.user, celda, request.POST.get("tipo", ""), request.POST.get("codigo"))
        return f"La celda {anterior} ahora es {celda.codigo} ({celda.get_tipo_display().lower()})."
    return _accion_celda(request, celda_id, accion)


@solo_administrador
@require_POST
def celda_estado(request, celda_id: int):
    """HU-035: inactivar con motivo o reactivar."""
    def accion(celda):
        if request.POST.get("activa") == "1":
            servicio_celdas.reactivar(request.user, celda)
            return f"Celda {celda.codigo} reactivada."
        servicio_celdas.inactivar(request.user, celda, request.POST.get("motivo", ""))
        return f"Celda {celda.codigo} inactivada."
    return _accion_celda(request, celda_id, accion)


@solo_administrador
@require_POST
def celda_eliminar(request, celda_id: int):
    """HU-036: eliminar una celda que nunca se usó."""
    return _accion_celda(request, celda_id,
                         lambda celda: f"Celda {servicio_celdas.eliminar(request.user, celda)} eliminada.")
