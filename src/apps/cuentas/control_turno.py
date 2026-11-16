"""Control de turno (Diseño iteración 2, sección 5; RN-31, RN-35, RN-36).

- BackendTurno: impide iniciar sesión fuera del turno o sin horario (UC-25).
- ControlTurnoMiddleware: cierra la sesión al terminar la jornada (UC-26), dejando completar
  un guardado en curso (RN-35a) y con 5 minutos de gracia (RN-35b).
- ajustar_duracion_sesion: la sesión de un operador dura como máximo 12 horas.
El script static/js/turno.js complementa esto en el navegador (avisos e inactividad).
"""
from datetime import datetime, timedelta
from urllib.parse import urlencode

from django.contrib.auth import logout
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.shortcuts import redirect
from django.urls import reverse

from apps.core import reloj

from . import turnos

CLAVE_FIN = "fin_jornada"
DURACION_MAXIMA_SESION = 12 * 3600


class BackendTurno(ModelBackend):
    """Solo actúa al iniciar sesión. No se usa user_can_authenticate porque Django también lo
    consulta en cada petición (get_user), y eso cerraría la sesión sin respetar RN-35."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        usuario = super().authenticate(request, username=username, password=password, **kwargs)
        if usuario is not None and not turnos.puede_ingresar(usuario, reloj.ahora()):
            return None
        return usuario


@receiver(user_logged_in)
def ajustar_duracion_sesion(sender, request, user, **kwargs):
    if not user.es_administrador():
        request.session.set_expiry(DURACION_MAXIMA_SESION)


def _ir_al_login(motivo: str):
    return redirect(f"{reverse('cuentas:login')}?{urlencode({'motivo': motivo})}")


class ControlTurnoMiddleware:
    RUTAS_LIBRES = ("/cuentas/salir/", "/cuentas/ingresar/", "/static/")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        usuario = getattr(request, "user", None)
        request.fin_jornada = None
        request.en_gracia = False
        if not usuario or not usuario.is_authenticated or usuario.es_administrador() or request.path.startswith(self.RUTAS_LIBRES):
            return self.get_response(request)

        ahora = reloj.ahora()
        fin = turnos.fin_de_jornada(usuario, ahora)
        if fin is not None:  # dentro del turno o de una autorización
            request.session[CLAVE_FIN] = fin.isoformat()
            request.fin_jornada = fin
            return self.get_response(request)

        # Fuera del turno con la sesión abierta (UC-26).
        fin_conocido = request.session.get(CLAVE_FIN)
        fin_jornada = datetime.fromisoformat(fin_conocido) if fin_conocido else ahora
        if not fin_conocido:
            request.session[CLAVE_FIN] = ahora.isoformat()
        request.fin_jornada = fin_jornada

        if request.method == "POST":
            # RN-35a: el registro en curso se guarda; si se guardó (redirección), se cierra la sesión.
            respuesta = self.get_response(request)
            if respuesta.status_code in (301, 302, 303):
                logout(request)
                return _ir_al_login("turno")
            return respuesta

        if ahora > fin_jornada + turnos.GRACIA:  # RN-35b: venció la gracia de 5 minutos
            logout(request)
            return _ir_al_login("turno")
        request.en_gracia = True
        return self.get_response(request)
