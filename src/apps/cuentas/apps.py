from django.apps import AppConfig


class CuentasConfig(AppConfig):
    name = "apps.cuentas"
    verbose_name = "Cuentas"

    def ready(self) -> None:
        from . import control_turno  # noqa: F401  registra la señal que limita la sesión a 12 horas
