"""Novedades ocurridas dentro de las instalaciones (RF-007, RN-14 a RN-16, RN-18)."""
from django.conf import settings
from django.db import models
from django.db.models import F, Q

from apps.entradas_salidas.models import Estadia


class TipoNovedad(models.TextChoices):
    ACCIDENTE = "ACCIDENTE", "Accidente"
    RAYON = "RAYON", "Rayón"
    CAIDA = "CAIDA", "Caída"
    DANO = "DANO", "Daño"
    OBSERVACION = "OBSERVACION", "Observación"  # CHG-002
    OTRO = "OTRO", "Otro"


class Novedad(models.Model):
    tipo = models.CharField(max_length=12, choices=TipoNovedad.choices)
    descripcion = models.TextField()
    fecha_hora_ocurrencia = models.DateTimeField()
    fecha_hora_registro = models.DateTimeField()
    registrado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="novedades_registradas")

    class Meta:
        db_table = "novedades_novedad"
        ordering = ["-fecha_hora_ocurrencia"]
        constraints = [
            models.CheckConstraint(condition=Q(tipo__in=TipoNovedad.values), name="ck_novedad_tipo"),
            models.CheckConstraint(condition=Q(fecha_hora_ocurrencia__lte=F("fecha_hora_registro")), name="ck_novedad_fechas"),
            models.CheckConstraint(condition=Q(descripcion__trim__length__gt=0), name="ck_novedad_descripcion"),
        ]
        indexes = [models.Index(fields=["fecha_hora_ocurrencia"], name="idx_novedad_ocurrencia")]

    @property
    def codigo(self) -> str:
        return f"N-{self.pk:04d}"


class NovedadEstadia(models.Model):
    """Asociativa N:M (DM-02). Clave primaria compuesta, como en el DDL aprobado."""

    pk = models.CompositePrimaryKey("novedad_id", "estadia_id")
    novedad = models.ForeignKey(Novedad, on_delete=models.PROTECT, related_name="vinculos")
    estadia = models.ForeignKey(Estadia, on_delete=models.PROTECT, related_name="vinculos_novedad")

    class Meta:
        db_table = "novedades_novedadestadia"
        indexes = [models.Index(fields=["estadia"], name="idx_novedadestadia_estadia")]
