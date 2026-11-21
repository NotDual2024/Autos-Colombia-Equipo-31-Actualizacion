"""Tarifas, descuentos, pagos de mensualidad y correos de confirmación (modelo de datos v1.4, iteración 3)."""
from datetime import date, datetime, timedelta

from django.conf import settings
from django.db import models
from django.db.models import F, Q

from apps.usuarios_celdas.models import Categoria, Vehiculo

VENTANA_CORRECCION_OPERADOR = timedelta(hours=24)  # RN-44 / P-50


class Tarifa(models.Model):
    categoria = models.CharField(max_length=15, choices=Categoria.choices)
    valor = models.PositiveIntegerField(help_text="Pesos colombianos (DM-06)")
    vigente_desde = models.DateField()

    class Meta:
        db_table = "pagos_tarifa"
        ordering = ["categoria", "-vigente_desde"]
        constraints = [
            models.UniqueConstraint(fields=["categoria", "vigente_desde"], name="uq_tarifa_categoria_vigencia"),
            models.CheckConstraint(condition=Q(categoria__in=Categoria.values), name="ck_tarifa_categoria"),
            models.CheckConstraint(condition=Q(valor__gt=0), name="ck_tarifa_valor"),
        ]

    def __str__(self) -> str:
        return f"{self.get_categoria_display()} {self.valor} desde {self.vigente_desde:%d/%m/%Y}"


class Descuento(models.Model):
    """RN-42: lo crea el administrador; no se edita (se deshabilita y se crea otro)."""

    descripcion = models.CharField(max_length=100)
    porcentaje = models.PositiveSmallIntegerField()
    habilitado = models.BooleanField(default=True)
    creado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="descuentos_creados")
    fecha_creacion = models.DateTimeField()

    class Meta:
        db_table = "pagos_descuento"
        ordering = ["-habilitado", "descripcion"]
        constraints = [
            models.CheckConstraint(condition=Q(porcentaje__gte=1, porcentaje__lte=100), name="ck_descuento_porcentaje"),
            models.CheckConstraint(condition=Q(descripcion__trim__length__gt=0), name="ck_descuento_descripcion"),
        ]

    def __str__(self) -> str:
        return f"{self.descripcion} ({self.porcentaje} %)"

    def valor_sobre(self, bruto: int) -> int:
        return valor_descuento(bruto, self.porcentaje)


def valor_descuento(bruto: int, porcentaje: int | None) -> int:
    """DM-16: redondeo hacia abajo al peso (igual que el CHECK de la base de datos)."""
    return (bruto * (porcentaje or 0)) // 100


class MedioPago(models.TextChoices):
    EFECTIVO = "EFECTIVO", "Efectivo"
    TRANSFERENCIA = "TRANSFERENCIA", "Transferencia"
    TARJETA = "TARJETA", "Tarjeta"


class EstadoPago(models.TextChoices):
    REGISTRADO = "REGISTRADO", "Registrado"
    CORREGIDO = "CORREGIDO", "Corregido"


class Pago(models.Model):
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.PROTECT, related_name="pagos")
    periodo_inicio = models.DateField()
    periodo_fin = models.DateField(help_text="Fecha de vencimiento")
    meses = models.PositiveSmallIntegerField(default=1)
    tarifa_unitaria = models.PositiveIntegerField(help_text="Copia de la tarifa al pagar (DM-15)")
    valor_bruto = models.PositiveIntegerField()
    descuento = models.ForeignKey(Descuento, on_delete=models.PROTECT, related_name="pagos", null=True, blank=True)
    porcentaje_descuento = models.PositiveSmallIntegerField(null=True, blank=True, help_text="Copia (DM-15)")
    valor = models.PositiveIntegerField(help_text="Valor cobrado (RN-41)")
    medio = models.CharField(max_length=13, choices=MedioPago.choices)
    numero_factura = models.PositiveIntegerField(unique=True)
    fecha_pago = models.DateTimeField()
    registrado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="pagos_registrados")
    estado = models.CharField(max_length=10, choices=EstadoPago.choices, default=EstadoPago.REGISTRADO)
    motivo_correccion = models.TextField(null=True, blank=True)
    corregido_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="pagos_corregidos",
                                      null=True, blank=True)
    fecha_correccion = models.DateTimeField(null=True, blank=True)
    corrige_a = models.OneToOneField("self", on_delete=models.PROTECT, related_name="reemplazo", null=True, blank=True)

    class Meta:
        db_table = "pagos_pago"
        constraints = [
            models.CheckConstraint(condition=Q(periodo_fin__gt=F("periodo_inicio")), name="ck_pago_periodo"),
            models.CheckConstraint(condition=Q(meses__gte=1, meses__lte=12), name="ck_pago_meses"),
            models.CheckConstraint(condition=Q(tarifa_unitaria__gt=0), name="ck_pago_tarifa"),
            models.CheckConstraint(condition=Q(valor__gte=0), name="ck_pago_valor"),
            models.CheckConstraint(condition=Q(numero_factura__gt=0), name="ck_pago_factura"),
            models.CheckConstraint(condition=Q(medio__in=MedioPago.values), name="ck_pago_medio"),
            models.CheckConstraint(condition=Q(estado__in=EstadoPago.values), name="ck_pago_estado"),
            models.CheckConstraint(
                condition=Q(porcentaje_descuento__isnull=True)
                | Q(porcentaje_descuento__gte=1, porcentaje_descuento__lte=100),
                name="ck_pago_porcentaje"),
            # RN-41: el valor lo calcula el sistema; la base de datos verifica la cuenta
            models.CheckConstraint(condition=Q(valor_bruto=F("tarifa_unitaria") * F("meses")), name="ck_pago_bruto"),
            models.CheckConstraint(
                condition=Q(porcentaje_descuento__isnull=True, valor=F("valor_bruto"))
                | Q(porcentaje_descuento__isnull=False,
                    valor=F("valor_bruto") - F("valor_bruto") * F("porcentaje_descuento") / 100),
                name="ck_pago_valor_calculado"),
            models.CheckConstraint(
                condition=Q(descuento__isnull=True, porcentaje_descuento__isnull=True)
                | Q(descuento__isnull=False, porcentaje_descuento__isnull=False),
                name="ck_pago_descuento"),
            # RN-44: un pago corregido tiene motivo, quién y cuándo; uno registrado no
            models.CheckConstraint(
                condition=Q(estado=EstadoPago.REGISTRADO, corregido_por__isnull=True, fecha_correccion__isnull=True,
                            motivo_correccion__isnull=True)
                | Q(estado=EstadoPago.CORREGIDO, corregido_por__isnull=False, fecha_correccion__isnull=False,
                    motivo_correccion__isnull=False, motivo_correccion__trim__length__gt=0),
                name="ck_pago_correccion"),
            models.CheckConstraint(condition=Q(corrige_a__isnull=True) | ~Q(corrige_a=F("id")), name="ck_pago_no_se_corrige"),
            models.UniqueConstraint(fields=["vehiculo", "periodo_inicio"], condition=Q(estado="REGISTRADO"),
                                    name="uq_pago_vehiculo_inicio"),
        ]
        indexes = [
            models.Index(fields=["vehiculo", "estado", "periodo_fin"], name="idx_pago_vehiculo_fin"),
            models.Index(fields=["fecha_pago"], name="idx_pago_fecha"),
        ]

    def __str__(self) -> str:
        return f"Factura {self.numero_factura_texto} · {self.vehiculo}"

    @property
    def numero_factura_texto(self) -> str:
        return f"{self.numero_factura:06d}"

    @property
    def esta_corregido(self) -> bool:
        return self.estado == EstadoPago.CORREGIDO

    def cubre(self, fecha: date) -> bool:
        return self.periodo_inicio <= fecha <= self.periodo_fin

    def valor_descuento(self) -> int:
        return self.valor_bruto - self.valor

    def corregible_por(self, usuario, momento: datetime) -> bool:
        """RN-44: el administrador siempre; el operador dentro de las 24 horas siguientes al registro."""
        if self.esta_corregido:
            return False
        return usuario.es_administrador() or momento - self.fecha_pago < VENTANA_CORRECCION_OPERADOR


class CorreoConfirmacion(models.Model):
    """RN-47 / DM-14: correo simulado de confirmación de pago."""

    pago = models.ForeignKey(Pago, on_delete=models.PROTECT, related_name="correos_confirmacion")
    destinatario = models.CharField(max_length=254)
    asunto = models.CharField(max_length=200)
    cuerpo = models.TextField()
    fecha_hora = models.DateTimeField()
    resultado = models.CharField(max_length=20)

    class Meta:
        db_table = "pagos_correoconfirmacion"
        ordering = ["-fecha_hora"]
        constraints = [
            models.CheckConstraint(condition=Q(resultado__in=["ENVIADO_SIMULADO", "FALLIDO"]), name="ck_confirmacion_resultado"),
        ]
        indexes = [models.Index(fields=["pago"], name="idx_confirmacion_pago")]


__all__ = ["Tarifa", "Descuento", "MedioPago", "EstadoPago", "Pago", "CorreoConfirmacion", "valor_descuento"]
