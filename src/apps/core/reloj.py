"""Reloj del sistema (Arquitectura 7.3).

Todo el código obtiene la fecha y hora actuales a través de este módulo, para
poder simular fechas en las pruebas y en los datos de demostración.
Uso en pruebas:  with mock.patch("apps.core.reloj.ahora", return_value=...):
"""
from datetime import date, datetime

from django.utils import timezone


def ahora() -> datetime:
    """Fecha y hora actuales en la zona horaria local (America/Bogota)."""
    return timezone.localtime(timezone.now())


def hoy() -> date:
    """Fecha actual en la zona horaria local."""
    return ahora().date()
