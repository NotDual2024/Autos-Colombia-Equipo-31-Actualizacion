"""Modelo de datos v1.5 (CHG-003): motivo de inactivación y formato del código de las celdas.

Las celdas que ya estuvieran inactivas reciben el motivo "Inactiva antes de CHG-003" (sección 9.3 del modelo).
"""
from django.db import migrations, models

from apps.usuarios_celdas.models import Celda


def motivo_para_inactivas(apps, schema_editor):
    apps.get_model("usuarios_celdas", "Celda").objects.filter(activa=False).update(
        motivo_inactivacion="Inactiva antes de CHG-003")


class Migration(migrations.Migration):

    dependencies = [
        ("usuarios_celdas", "0003_motivo_inactivacion"),
    ]

    operations = [
        migrations.AddField(model_name="celda", name="motivo_inactivacion",
                            field=models.CharField(blank=True, max_length=100, null=True)),
        migrations.RunPython(motivo_para_inactivas, migrations.RunPython.noop),
        *[migrations.AddConstraint(model_name="celda", constraint=c)
          for c in Celda._meta.constraints if c.name in ("ck_celda_codigo", "ck_celda_motivo")],
    ]
