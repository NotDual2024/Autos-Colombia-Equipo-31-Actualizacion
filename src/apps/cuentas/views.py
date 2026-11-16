"""Inicio de sesión (UC-01) y gestión de operadores (HU-010 / UC-15; mockup M-12)."""
from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from apps.core.errores import ErrorNegocio

from . import services
from .forms import FormularioInicioSesion
from .models import Rol, Usuario
from .permisos import solo_administrador


class InicioSesionView(auth_views.LoginView):
    template_name = "cuentas/login.html"
    authentication_form = FormularioInicioSesion
    redirect_authenticated_user = True


class CierreSesionView(auth_views.LogoutView):
    pass


@solo_administrador
@require_http_methods(["GET", "POST"])
def operadores(request):
    datos = {"nombre": "", "usuario": ""}
    error = None
    if request.method == "POST":
        datos = {"nombre": request.POST.get("nombre", ""), "usuario": request.POST.get("usuario", "")}
        try:
            operador = services.crear_operador(request.user, datos["nombre"], datos["usuario"], request.POST.get("clave", ""))
            messages.success(request, f"Operador {operador.username} creado. Ya puede iniciar sesión.")
            return redirect("cuentas:operadores")
        except ErrorNegocio as e:
            error = e.mensaje
    lista = Usuario.objects.filter(rol=Rol.OPERADOR).order_by("-is_active", "username")
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


def acceso_denegado(request, exception=None):
    return render(request, "403.html", status=403)
