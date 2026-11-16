"""Consultas de solo lectura sobre vehículos y celdas."""
import re

from .models import Vehiculo


def normalizar_placa(texto: str) -> str:
    """Mayúsculas y sin espacios ni guiones (RN-23)."""
    return re.sub(r"[\s\-]", "", (texto or "")).upper()


def vehiculo_por_placa(placa: str) -> Vehiculo | None:
    return Vehiculo.objects.select_related("propietario").filter(placa=normalizar_placa(placa)).first()
