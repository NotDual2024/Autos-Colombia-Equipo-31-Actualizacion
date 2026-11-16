"""Avisos de retiro (simulados) y contactos con autoridades (RF-009 a RF-012)."""
from django.conf import settings
from django.db import models
from django.db.models import Q

from apps.pagos.models import Pago


class OrigenAviso(models.TextChoices):
    AUTOMATICO = "AUTOMATICO", "Automático"
    MANUAL = "MANUAL", "Manual"


class ResultadoEnvio(models.TextChoices):
    ENVIADO_SIMULADO = "ENVIADO_SIMULADO", "Enviado (simulado)"
    FALLIDO = "FALLIDO", "Fallido"


class AvisoCorreo(models.Model):
    """Cada intento de enviar el correo de retiro de un vencimiento (DM-03)."""

    pago = models.ForeignKey(Pago, on_delete=models.PROTECT, related_name="avisos")
    numero_envio = models.PositiveSmallIntegerField(null=True, blank=True, help_text="1 = primero, 2 = reenvío; nulo si falló")
    origen = models.CharField(max_length=10, choices=OrigenAviso.choices)
    enviado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="avisos_enviados", null=True, blank=True
    )
    destinatario = models.EmailField(max_length=254)
    asunto = models.CharField(max_length=200)
    cuerpo = models.TextField()
    fecha_hora = models.DateTimeField()
    resultado = models.CharField(max_length=20, choices=ResultadoEnvio.choices)

    class Meta:
        db_table = "notificaciones_avisocorreo"
        ordering = ["fecha_hora"]
        constraints = [
            # RN-11 y RN-22: como máximo un primer correo y un reenvío exitosos por vencimiento
            models.UniqueConstraint(
                fields=["pago", "numero_envio"], condition=Q(numero_envio__isnull=False), name="uq_aviso_envio"
            ),
            models.CheckConstraint(condition=Q(numero_envio__isnull=True) | Q(numero_envio__in=[1, 2]), name="ck_aviso_numero"),
            models.CheckConstraint(condition=Q(origen__in=OrigenAviso.values), name="ck_aviso_origen"),
            models.CheckConstraint(condition=Q(resultado__in=ResultadoEnvio.values), name="ck_aviso_resultado"),
            models.CheckConstraint(
                condition=Q(origen=OrigenAviso.MANUAL, enviado_por__isnull=False)
                | Q(origen=OrigenAviso.AUTOMATICO, enviado_por__isnull=True),
                name="ck_aviso_manual_usuario",
            ),
            models.CheckConstraint(
                condition=Q(resultado=ResultadoEnvio.ENVIADO_SIMULADO, numero_envio__isnull=False)
                | Q(resultado=ResultadoEnvio.FALLIDO, numero_envio__isnull=True),
                name="ck_aviso_exitoso_numero",
            ),
        ]


class ContactoAutoridad(models.Model):
    """Registro del contacto con autoridades (RF-011). Solo administrador; se permiten varios (P-25)."""

    pago = models.ForeignKey(Pago, on_delete=models.PROTECT, related_name="contactos_autoridad")
    fecha_hora = models.DateTimeField()
    registrado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="contactos_registrados")
    observacion = models.TextField()

    class Meta:
        db_table = "notificaciones_contactoautoridad"
        ordering = ["fecha_hora"]
        constraints = [
            models.CheckConstraint(condition=Q(observacion__trim__length__gt=0), name="ck_contacto_observacion"),
        ]
        indexes = [models.Index(fields=["pago"], name="idx_contacto_pago")]
