from django import forms
from django.contrib.auth.forms import AuthenticationForm


class FormularioInicioSesion(AuthenticationForm):
    """Mensaje único para usuario o contraseña inválidos (no revela cuál falló)."""

    error_messages = {
        "invalid_login": "Usuario o contraseña incorrectos. Verifica tus datos e inténtalo de nuevo.",
        "inactive": "Usuario o contraseña incorrectos. Verifica tus datos e inténtalo de nuevo.",
    }

    username = forms.CharField(label="Usuario", widget=forms.TextInput(attrs={"autofocus": True, "placeholder": "Ej. mrodriguez"}))
    password = forms.CharField(label="Contraseña", strip=False, widget=forms.PasswordInput(attrs={"placeholder": "Ingresa tu contraseña"}))
