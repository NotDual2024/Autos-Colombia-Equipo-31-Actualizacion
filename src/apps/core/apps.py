from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = "apps.core"
    verbose_name = "Núcleo"

    def ready(self) -> None:
        # Registra los lookups personalizados (__glob, __length) antes de usarlos.
        from . import lookups  # noqa: F401
