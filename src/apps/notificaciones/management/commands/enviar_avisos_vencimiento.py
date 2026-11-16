from django.core.management.base import BaseCommand

from apps.notificaciones import services


class Command(BaseCommand):
    help = "Envía (simulado) el primer correo de cada mensualidad vencida con el vehículo dentro (UC-11). Es idempotente."

    def handle(self, *args, **opciones):
        enviados = services.enviar_automaticos()
        self.stdout.write(self.style.SUCCESS(f"Avisos automáticos enviados: {enviados}"))
