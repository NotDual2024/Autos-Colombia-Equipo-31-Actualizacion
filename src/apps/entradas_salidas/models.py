"""Estadías: entrada y salida de un vehículo en una celda (RF-001, RF-004)."""
from datetime import datetime

from django.conf import settings
from django.db import models
from django.db.models import F, Q

from apps.usuarios_celdas.models import Celda, Vehiculo


class Estadia(models.Model):
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.PROTECT, related_name="estadias")
    celda = models.ForeignKey(Celda, on_delete=models.PROTECT, related_name="estadias")
    fecha_hora_entrada = models.DateTimeField()
    usuario_entrada = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="entradas_registradas")
    fecha_hora_salida = models.DateTimeField(null=True, blank=True)
    usuario_salida = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="salidas_registradas", null=True, blank=True
    )

    class Meta:
        db_table = "entradas_salidas_estadia"
        constraints = [
            # RN-04: un vehículo con como máximo una estadía abierta
            models.UniqueConstraint(fields=["vehiculo"], condition=Q(fecha_hora_salida__isnull=True), name="uq_estadia_vehiculo_abierta"),
            # RN-05: una celda con como máximo una estadía abierta
            models.UniqueConstraint(fields=["celda"], condition=Q(fecha_hora_salida__isnull=True), name="uq_estadia_celda_abierta"),
            models.CheckConstraint(
                condition=Q(fecha_hora_salida__isnull=True) | Q(fecha_hora_salida__gt=F("fecha_hora_entrada")),
                name="ck_estadia_salida_posterior",
            ),
            models.CheckConstraint(
                condition=Q(fecha_hora_salida__isnull=True, usuario_salida__isnull=True)
                | Q(fecha_hora_salida__isnull=False, usuario_salida__isnull=False),
                name="ck_estadia_salida_completa",
            ),
        ]
        indexes = [
            models.Index(fields=["vehiculo", "fecha_hora_entrada"], name="idx_estadia_vehiculo_entrada"),
            models.Index(fields=["fecha_hora_entrada"], name="idx_estadia_entrada"),
        ]

    def esta_abierta(self) -> bool:
        return self.fecha_hora_salida is None

    def incluye(self, momento: datetime) -> bool:
        """El vehículo estaba dentro en ese momento (RF-007)."""
        if momento < self.fecha_hora_entrada:
            return False
        return self.fecha_hora_salida is None or momento <= self.fecha_hora_salida
