"""Tarifas y pagos de mensualidad (pantallas en la iteración 3)."""
from datetime import date

from django.conf import settings
from django.db import models
from django.db.models import F, Q

from apps.usuarios_celdas.models import Categoria, Vehiculo


class Tarifa(models.Model):
    categoria = models.CharField(max_length=15, choices=Categoria.choices)
    valor = models.PositiveIntegerField(help_text="Pesos colombianos (DM-06)")
    vigente_desde = models.DateField()

    class Meta:
        db_table = "pagos_tarifa"
        constraints = [
            models.UniqueConstraint(fields=["categoria", "vigente_desde"], name="uq_tarifa_categoria_vigencia"),
            models.CheckConstraint(condition=Q(categoria__in=Categoria.values), name="ck_tarifa_categoria"),
            models.CheckConstraint(condition=Q(valor__gt=0), name="ck_tarifa_valor"),
        ]


class Pago(models.Model):
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.PROTECT, related_name="pagos")
    periodo_inicio = models.DateField()
    periodo_fin = models.DateField(help_text="Fecha de vencimiento")
    valor = models.PositiveIntegerField(help_text="Copia de la tarifa al pagar (DM-04)")
    fecha_pago = models.DateTimeField()
    registrado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="pagos_registrados")

    class Meta:
        db_table = "pagos_pago"
        constraints = [
            models.CheckConstraint(condition=Q(periodo_fin__gte=F("periodo_inicio")), name="ck_pago_periodo"),
            models.CheckConstraint(condition=Q(valor__gt=0), name="ck_pago_valor"),
        ]
        indexes = [models.Index(fields=["vehiculo", "periodo_fin"], name="idx_pago_vehiculo_fin")]

    def cubre(self, fecha: date) -> bool:
        return self.periodo_inicio <= fecha <= self.periodo_fin
