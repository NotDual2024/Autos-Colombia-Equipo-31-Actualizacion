"""Modelo de datos v1.4: motivo de inactivación de propietarios y vehículos (RN-46).

Los registros que ya estaban inactivos reciben el motivo OTRO (sección 8.3 del modelo).
"""
from django.db import migrations, models

from apps.usuarios_celdas.models import _restricciones_inactivacion

MOTIVOS = [("FALTA_PAGO", "Falta de pago"), ("OTRO", "Otro")]
DESCRIPCION_ANTERIOR = "Inactivado antes de la iteración 3"


def motivo_para_inactivos(apps, schema_editor):
    for modelo in ("Propietario", "Vehiculo"):
        apps.get_model("usuarios_celdas", modelo).objects.filter(activo=False).update(
            motivo_inactivacion="OTRO", descripcion_inactivacion=DESCRIPCION_ANTERIOR)


class Migration(migrations.Migration):

    dependencies = [
        ("usuarios_celdas", "0002_historialpropiedad_solicitudcambiopropietario_and_more"),
    ]

    operations = [
        migrations.AddField(model_name="propietario", name="motivo_inactivacion",
                            field=models.CharField(blank=True, choices=MOTIVOS, max_length=12, null=True)),
        migrations.AddField(model_name="propietario", name="descripcion_inactivacion",
                            field=models.CharField(blank=True, max_length=200, null=True)),
        migrations.AddField(model_name="vehiculo", name="motivo_inactivacion",
                            field=models.CharField(blank=True, choices=MOTIVOS, max_length=12, null=True)),
        migrations.AddField(model_name="vehiculo", name="descripcion_inactivacion",
                            field=models.CharField(blank=True, max_length=200, null=True)),
        migrations.RunPython(motivo_para_inactivos, migrations.RunPython.noop),
        *[migrations.AddConstraint(model_name="propietario", constraint=c) for c in _restricciones_inactivacion("propietario")],
        *[migrations.AddConstraint(model_name="vehiculo", constraint=c) for c in _restricciones_inactivacion("vehiculo")],
    ]
