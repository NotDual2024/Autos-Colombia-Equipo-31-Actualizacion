"""Modelo de datos v1.4: descuentos, datos nuevos del pago, corrección y correo de confirmación (iteración 3).

Los pagos existentes quedan como 1 mes, en efectivo, sin descuento, registrados y con su id como número de
factura (sección 8.3 del modelo).
"""
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

from apps.pagos.models import CorreoConfirmacion, Descuento, Pago

MEDIOS = [("EFECTIVO", "Efectivo"), ("TRANSFERENCIA", "Transferencia"), ("TARJETA", "Tarjeta")]
ESTADOS = [("REGISTRADO", "Registrado"), ("CORREGIDO", "Corregido")]


def completar_pagos_existentes(apps, schema_editor):
    Modelo = apps.get_model("pagos", "Pago")
    for pago in Modelo.objects.all():
        pago.meses = 1
        pago.tarifa_unitaria = pago.valor
        pago.valor_bruto = pago.valor
        pago.medio = "EFECTIVO"
        pago.numero_factura = pago.pk
        pago.estado = "REGISTRADO"
        pago.save(update_fields=["meses", "tarifa_unitaria", "valor_bruto", "medio", "numero_factura", "estado"])


class Migration(migrations.Migration):

    dependencies = [
        ("pagos", "0001_initial"),
        ("usuarios_celdas", "0003_motivo_inactivacion"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Descuento",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("descripcion", models.CharField(max_length=100)),
                ("porcentaje", models.PositiveSmallIntegerField()),
                ("habilitado", models.BooleanField(default=True)),
                ("fecha_creacion", models.DateTimeField()),
                ("creado_por", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="descuentos_creados",
                                                 to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "pagos_descuento", "ordering": ["-habilitado", "descripcion"],
                     "constraints": list(Descuento._meta.constraints)},
        ),
        migrations.AlterModelOptions(name="tarifa", options={"ordering": ["categoria", "-vigente_desde"]}),
        migrations.RemoveConstraint(model_name="pago", name="ck_pago_periodo"),
        migrations.RemoveConstraint(model_name="pago", name="ck_pago_valor"),
        migrations.RemoveIndex(model_name="pago", name="idx_pago_vehiculo_fin"),
        # Columnas nuevas, primero opcionales para completar los pagos existentes
        migrations.AddField(model_name="pago", name="meses", field=models.PositiveSmallIntegerField(default=1)),
        migrations.AddField(model_name="pago", name="tarifa_unitaria", field=models.PositiveIntegerField(null=True)),
        migrations.AddField(model_name="pago", name="valor_bruto", field=models.PositiveIntegerField(null=True)),
        migrations.AddField(model_name="pago", name="porcentaje_descuento",
                            field=models.PositiveSmallIntegerField(blank=True, help_text="Copia (DM-15)", null=True)),
        migrations.AddField(model_name="pago", name="descuento",
                            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                                                    related_name="pagos", to="pagos.descuento")),
        migrations.AddField(model_name="pago", name="medio", field=models.CharField(choices=MEDIOS, max_length=13, null=True)),
        migrations.AddField(model_name="pago", name="numero_factura", field=models.PositiveIntegerField(null=True)),
        migrations.AddField(model_name="pago", name="estado",
                            field=models.CharField(choices=ESTADOS, default="REGISTRADO", max_length=10)),
        migrations.AddField(model_name="pago", name="motivo_correccion", field=models.TextField(blank=True, null=True)),
        migrations.AddField(model_name="pago", name="corregido_por",
                            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                                                    related_name="pagos_corregidos", to=settings.AUTH_USER_MODEL)),
        migrations.AddField(model_name="pago", name="fecha_correccion", field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name="pago", name="corrige_a",
                            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                                                       related_name="reemplazo", to="pagos.pago")),
        migrations.RunPython(completar_pagos_existentes, migrations.RunPython.noop),
        migrations.AlterField(model_name="pago", name="tarifa_unitaria",
                              field=models.PositiveIntegerField(help_text="Copia de la tarifa al pagar (DM-15)")),
        migrations.AlterField(model_name="pago", name="valor_bruto", field=models.PositiveIntegerField()),
        migrations.AlterField(model_name="pago", name="valor", field=models.PositiveIntegerField(help_text="Valor cobrado (RN-41)")),
        migrations.AlterField(model_name="pago", name="medio", field=models.CharField(choices=MEDIOS, max_length=13)),
        migrations.AlterField(model_name="pago", name="numero_factura", field=models.PositiveIntegerField(unique=True)),
        *[migrations.AddConstraint(model_name="pago", constraint=c) for c in Pago._meta.constraints],
        *[migrations.AddIndex(model_name="pago", index=i) for i in Pago._meta.indexes],
        migrations.CreateModel(
            name="CorreoConfirmacion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("destinatario", models.CharField(max_length=254)),
                ("asunto", models.CharField(max_length=200)),
                ("cuerpo", models.TextField()),
                ("fecha_hora", models.DateTimeField()),
                ("resultado", models.CharField(max_length=20)),
                ("pago", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="correos_confirmacion",
                                           to="pagos.pago")),
            ],
            options={"db_table": "pagos_correoconfirmacion", "ordering": ["-fecha_hora"],
                     "constraints": list(CorreoConfirmacion._meta.constraints),
                     "indexes": list(CorreoConfirmacion._meta.indexes)},
        ),
    ]
