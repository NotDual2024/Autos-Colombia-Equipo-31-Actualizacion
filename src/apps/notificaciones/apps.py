from django.apps import AppConfig


class NotificacionesConfig(AppConfig):
    name = "apps.notificaciones"
    verbose_name = "Notificaciones"

    def ready(self) -> None:
        from . import planificador

        planificador.iniciar()
