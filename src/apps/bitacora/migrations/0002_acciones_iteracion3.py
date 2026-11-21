"""Modelo de datos v1.4: acciones y entidades nuevas de la bitácora (iteración 3)."""
from django.db import migrations, models

ACCIONES = [
    ("CREAR", "Registrar"), ("MODIFICAR", "Modificar"), ("ACTIVAR", "Activar"), ("INACTIVAR", "Inactivar"),
    ("SOLICITAR_CAMBIO", "Solicitar cambio de propietario"), ("APROBAR_CAMBIO", "Aprobar cambio de propietario"),
    ("RECHAZAR_CAMBIO", "Rechazar cambio de propietario"), ("RESTABLECER_CLAVE", "Restablecer contraseña"),
    ("ASIGNAR_HORARIO", "Asignar franja de horario"), ("QUITAR_HORARIO", "Quitar franja de horario"),
    ("AUTORIZAR_FUERA_TURNO", "Autorizar ingreso fuera de turno"), ("CORREGIR_PAGO", "Corregir pago"),
    ("HABILITAR", "Habilitar"), ("DESHABILITAR", "Deshabilitar"),
]
ENTIDADES = [
    ("PROPIETARIO", "Propietario"), ("VEHICULO", "Vehículo"), ("OPERADOR", "Operador"), ("HORARIO", "Horario"),
    ("AUTORIZACION", "Autorización"), ("SOLICITUD_CAMBIO", "Solicitud de cambio"), ("PAGO", "Pago"),
    ("TARIFA", "Tarifa"), ("DESCUENTO", "Descuento"),
]


class Migration(migrations.Migration):

    dependencies = [
        ("bitacora", "0001_initial"),
    ]

    operations = [
        migrations.RemoveConstraint(model_name="registrooperacion", name="ck_bitacora_accion"),
        migrations.RemoveConstraint(model_name="registrooperacion", name="ck_bitacora_entidad"),
        migrations.AlterField(model_name="registrooperacion", name="accion",
                              field=models.CharField(choices=ACCIONES, max_length=25)),
        migrations.AlterField(model_name="registrooperacion", name="entidad",
                              field=models.CharField(choices=ENTIDADES, max_length=20)),
        migrations.AddConstraint(model_name="registrooperacion", constraint=models.CheckConstraint(
            condition=models.Q(accion__in=[a for a, _ in ACCIONES]), name="ck_bitacora_accion")),
        migrations.AddConstraint(model_name="registrooperacion", constraint=models.CheckConstraint(
            condition=models.Q(entidad__in=[e for e, _ in ENTIDADES]), name="ck_bitacora_entidad")),
    ]
