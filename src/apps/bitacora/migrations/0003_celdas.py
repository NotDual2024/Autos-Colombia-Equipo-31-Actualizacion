"""Modelo de datos v1.5 (CHG-003): acción ELIMINAR y entidad CELDA en la bitácora."""
from django.db import migrations

from apps.bitacora.migrations import _opciones


class Migration(migrations.Migration):

    dependencies = [
        ("bitacora", "0002_acciones_iteracion3"),
    ]

    operations = _opciones.operaciones(
        acciones_extra=[("ELIMINAR", "Eliminar")], entidades_extra=[("CELDA", "Celda")])
