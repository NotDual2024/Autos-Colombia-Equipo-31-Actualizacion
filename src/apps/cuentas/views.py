"""Inicio de sesión (UC-01, UC-25) y administración de operadores, horarios y autorizaciones
(HU-010, HU-019, HU-020, HU-022; mockups M-12, M-21, M-22, M-24)."""
from datetime import datetime, time

from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST

from apps.core import reloj
from apps.core.errores import ErrorNegocio

from . import services, turnos
from .forms import FormularioInicioSesion
from .models import DIAS, AutorizacionFueraTurno, Rol, Usuario
from .permisos import solo_administrador


class InicioSesionView(auth_views.LoginView):
    template_name = "cuentas/login.html"
    authentication_form = FormularioInicioSesion
    redirect_authenticated_user = True

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        motivo = self.request.GET.get("motivo")
        if motivo == "turno":
            contexto["aviso"] = "Tu turno terminó y la sesión se cerró."
        elif motivo == "inactividad":
            contexto["aviso"] = "La sesión se cerró por fin de turno e inactividad."
        return contexto


class CierreSesionView(auth_views.LogoutView):
    pass


def _hora(texto: str) -> time | None:
    try:
        return datetime.strptime(texto, "%H:%M").time()
    except (TypeError, ValueError):
        return None


def _fecha_hora(texto: str) -> datetime | None:
    try:
        return timezone.make_aware(datetime.fromisoformat(texto))
    except (TypeError, ValueError):
        return None


@solo_administrador
@require_http_methods(["GET", "POST"])
def operadores(request):
    """M-12 / M-21."""
    datos = {"nombre": "", "usuario": ""}
    error = None
    if request.method == "POST":
        datos = {"nombre": request.POST.get("nombre", ""), "usuario": request.POST.get("usuario", "")}
        try:
            operador = services.crear_operador(request.user, datos["nombre"], datos["usuario"], request.POST.get("clave", ""))
            messages.success(request, f"Operador {operador.username} creado. Asígnale un horario para que pueda iniciar sesión.")
            return redirect("cuentas:horario", operador_id=operador.pk)
        except ErrorNegocio as e:
            error = e.mensaje
    lista = Usuario.objects.filter(rol=Rol.OPERADOR).prefetch_related("horarios").order_by("-is_active", "username")
    return render(request, "cuentas/operadores.html", {"operadores": lista, "datos": datos, "error": error})


@solo_administrador
@require_POST
def cambiar_estado(request, operador_id: int):
    activar = request.POST.get("activar") == "1"
    try:
        operador = services.cambiar_estado(request.user, operador_id, activar)
        messages.success(request, f"Operador {operador.username} {'reactivado' if activar else 'desactivado'}.")
    except ErrorNegocio as e:
        messages.error(request, e.mensaje)
    return redirect("cuentas:operadores")


@solo_administrador
@require_http_methods(["GET", "POST"])
def editar_operador(request, operador_id: int):
    """M-21 / HU-019: editar el nombre y restablecer la contraseña."""
    operador = get_object_or_404(Usuario, pk=operador_id, rol=Rol.OPERADOR)
    error = None
    if request.method == "POST":
        try:
            if request.POST.get("accion") == "clave":
                services.restablecer_clave(request.user, operador.pk, request.POST.get("clave", ""), request.POST.get("confirmacion", ""))
                messages.success(request, f"Contraseña de {operador.username} restablecida.")
            else:
                services.editar_nombre(request.user, operador.pk, request.POST.get("nombre", ""))
                messages.success(request, "Nombre actualizado.")
            return redirect("cuentas:operadores")
        except ErrorNegocio as e:
            error = e.mensaje
    return render(request, "cuentas/editar_operador.html", {"operador": operador, "error": error})


@solo_administrador
@require_http_methods(["GET", "POST"])
def horario(request, operador_id: int):
    """M-22 / HU-020."""
    operador = get_object_or_404(Usuario, pk=operador_id, rol=Rol.OPERADOR)
    error = None
    if request.method == "POST":
        try:
            if request.POST.get("quitar"):
                turnos.quitar_franja(request.user, int(request.POST["quitar"]))
                messages.success(request, "Franja quitada.")
            else:
                inicio, fin = _hora(request.POST.get("inicio")), _hora(request.POST.get("fin"))
                if inicio is None or fin is None:
                    raise ErrorNegocio("Indica la hora de inicio y la de fin.")
                turnos.asignar_franja(request.user, operador.pk, int(request.POST.get("dia", 0)), inicio, fin)
                messages.success(request, "Franja asignada.")
            return redirect("cuentas:horario", operador_id=operador.pk)
        except (ErrorNegocio, ValueError) as e:
            error = getattr(e, "mensaje", "Datos inválidos.")
    franjas = list(operador.horarios.all())
    por_dia = [(n, nombre, [f for f in franjas if f.dia_semana == n]) for n, nombre in DIAS.items()]
    return render(request, "cuentas/horario.html", {
        "operador": operador, "por_dia": por_dia, "dias": DIAS.items(), "error": error, "datos": request.POST,
    })


@solo_administrador
@require_http_methods(["GET", "POST"])
def autorizaciones(request):
    """M-24 / HU-022."""
    error = None
    if request.method == "POST":
        try:
            desde, hasta = _fecha_hora(request.POST.get("desde")), _fecha_hora(request.POST.get("hasta"))
            if desde is None or hasta is None:
                raise ErrorNegocio("Indica la fecha y hora de inicio y de fin.")
            turnos.autorizar(request.user, int(request.POST.get("operador", 0)), desde, hasta, request.POST.get("motivo", ""))
            messages.success(request, "Autorización registrada.")
            return redirect("cuentas:autorizaciones")
        except (ErrorNegocio, ValueError) as e:
            error = getattr(e, "mensaje", "Datos inválidos.")
    ahora = reloj.ahora()
    return render(request, "cuentas/autorizaciones.html", {
        "operadores": Usuario.objects.filter(rol=Rol.OPERADOR, is_active=True).order_by("username"),
        "autorizaciones": AutorizacionFueraTurno.objects.select_related("operador", "autorizado_por")[:50],
        "ahora": ahora, "ahora_local": ahora.strftime("%Y-%m-%dT%H:%M"), "error": error, "datos": request.POST,
    })


def acceso_denegado(request, exception=None):
    return render(request, "403.html", status=403)
