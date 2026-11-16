from django import forms
from django.contrib.auth.forms import AuthenticationForm

from apps.core import reloj

from . import turnos
from .models import Usuario


class FormularioInicioSesion(AuthenticationForm):
    """Mensaje único para usuario o contraseña inválidos (no revela cuál falló).

    Si las credenciales son correctas pero el operador está fuera de turno o sin horario,
    muestra ese motivo (UC-25, HU-021).
    """

    error_messages = {
        "invalid_login": "Usuario o contraseña incorrectos. Verifica tus datos e inténtalo de nuevo.",
        "inactive": "Usuario o contraseña incorrectos. Verifica tus datos e inténtalo de nuevo.",
    }

    username = forms.CharField(label="Usuario", widget=forms.TextInput(attrs={"autofocus": True, "placeholder": "Ej. mrodriguez"}))
    password = forms.CharField(label="Contraseña", strip=False, widget=forms.PasswordInput(attrs={"placeholder": "Ingresa tu contraseña"}))

    def clean(self):
        try:
            return super().clean()
        except forms.ValidationError:
            usuario = Usuario.objects.filter(username=self.cleaned_data.get("username")).first()
            if usuario and usuario.is_active and usuario.check_password(self.cleaned_data.get("password") or ""):
                motivo = turnos.motivo_bloqueo(usuario, reloj.ahora())
                if motivo:
                    raise forms.ValidationError(motivo + ".", code="fuera_de_turno")
            raise
