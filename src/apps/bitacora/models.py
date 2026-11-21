"""Bitácora de operaciones (RF-111, RN-34, DEC-013, DM-08, DM-10).

Solo depende de core: el usuario se referencia con settings.AUTH_USER_MODEL (DM-08 corregida),
así cuentas y usuarios_celdas pueden registrar operaciones sin formar un ciclo.
"""
from django.conf import settings
from django.db import models
from django.db.models import Q


class Accion(models.TextChoices):
    CREAR = "CREAR", "Registrar"
    MODIFICAR = "MODIFICAR", "Modificar"
    ACTIVAR = "ACTIVAR", "Activar"
    INACTIVAR = "INACTIVAR", "Inactivar"
    SOLICITAR_CAMBIO = "SOLICITAR_CAMBIO", "Solicitar cambio de propietario"
    APROBAR_CAMBIO = "APROBAR_CAMBIO", "Aprobar cambio de propietario"
    RECHAZAR_CAMBIO = "RECHAZAR_CAMBIO", "Rechazar cambio de propietario"
    RESTABLECER_CLAVE = "RESTABLECER_CLAVE", "Restablecer contraseña"
    ASIGNAR_HORARIO = "ASIGNAR_HORARIO", "Asignar franja de horario"
    QUITAR_HORARIO = "QUITAR_HORARIO", "Quitar franja de horario"
    AUTORIZAR_FUERA_TURNO = "AUTORIZAR_FUERA_TURNO", "Autorizar ingreso fuera de turno"
    CORREGIR_PAGO = "CORREGIR_PAGO", "Corregir pago"
    HABILITAR = "HABILITAR", "Habilitar"
    DESHABILITAR = "DESHABILITAR", "Deshabilitar"


class Entidad(models.TextChoices):
    PROPIETARIO = "PROPIETARIO", "Propietario"
    VEHICULO = "VEHICULO", "Vehículo"
    OPERADOR = "OPERADOR", "Operador"
    HORARIO = "HORARIO", "Horario"
    AUTORIZACION = "AUTORIZACION", "Autorización"
    SOLICITUD_CAMBIO = "SOLICITUD_CAMBIO", "Solicitud de cambio"
    PAGO = "PAGO", "Pago"
    TARIFA = "TARIFA", "Tarifa"
    DESCUENTO = "DESCUENTO", "Descuento"


class RegistroOperacion(models.Model):
    fecha_hora = models.DateTimeField()
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="operaciones")
    accion = models.CharField(max_length=25, choices=Accion.choices)
    entidad = models.CharField(max_length=20, choices=Entidad.choices)
    entidad_id = models.PositiveIntegerField()
    descripcion = models.CharField(max_length=255)
    detalle = models.JSONField(null=True, blank=True, help_text='{"campo": ["antes", "después"]}')

    class Meta:
        db_table = "bitacora_registrooperacion"
        ordering = ["-fecha_hora", "-id"]
        constraints = [
            models.CheckConstraint(condition=Q(accion__in=Accion.values), name="ck_bitacora_accion"),
            models.CheckConstraint(condition=Q(entidad__in=Entidad.values), name="ck_bitacora_entidad"),
        ]
        indexes = [
            models.Index(fields=["entidad", "entidad_id"], name="idx_bitacora_entidad"),
            models.Index(fields=["usuario", "fecha_hora"], name="idx_bitacora_usuario_fecha"),
            models.Index(fields=["fecha_hora"], name="idx_bitacora_fecha"),
        ]
