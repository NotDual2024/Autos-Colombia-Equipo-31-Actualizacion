"""Propietarios, vehículos y celdas (modelo de datos v1.1; pantallas en la iteración 2)."""
from django.conf import settings
from django.db import models
from django.db.models import F, Q


class TipoVehiculo(models.TextChoices):
    MOTO = "MOTO", "Moto"
    CARRO = "CARRO", "Carro"
    CAMIONETA = "CAMIONETA", "Camioneta"


class Categoria(models.TextChoices):
    """Categoría de celda y de tarifa (RN-08, RN-19)."""

    MOTO = "MOTO", "Moto"
    CARRO_CAMIONETA = "CARRO_CAMIONETA", "Carro / camioneta"


# RN-23: formatos de placa (mayúsculas, sin espacios)
PATRONES_PLACA = {
    "CARRO": "[A-Z][A-Z][A-Z][0-9][0-9][0-9]",
    "MOTO": "[A-Z][A-Z][A-Z][0-9][0-9][A-Z]",
    "MOTO_ANTIGUA": "[A-Z][A-Z][A-Z][0-9][0-9]",
}


PATRON_CELULAR = "3" + "[0-9]" * 9


class MotivoInactivacion(models.TextChoices):
    """RN-46: motivo de la inactivación de un propietario o vehículo."""

    FALTA_PAGO = "FALTA_PAGO", "Falta de pago"
    OTRO = "OTRO", "Otro"


def _restricciones_inactivacion(prefijo: str) -> list:
    return [
        models.CheckConstraint(condition=Q(motivo_inactivacion__isnull=True) | Q(motivo_inactivacion__in=MotivoInactivacion.values),
                               name=f"ck_{prefijo}_motivo_valor"),
        models.CheckConstraint(condition=Q(activo=True, motivo_inactivacion__isnull=True)
                               | Q(activo=False, motivo_inactivacion__isnull=False), name=f"ck_{prefijo}_motivo_estado"),
        models.CheckConstraint(condition=Q(motivo_inactivacion="OTRO", descripcion_inactivacion__isnull=False,
                                 descripcion_inactivacion__trim__length__gt=0)
                               | (~Q(motivo_inactivacion="OTRO") | Q(motivo_inactivacion__isnull=True))
                               & (Q(descripcion_inactivacion__isnull=True) | Q(descripcion_inactivacion="")),
                               name=f"ck_{prefijo}_motivo_descripcion"),
    ]


class ConMotivoInactivacion(models.Model):
    activo = models.BooleanField(default=True)
    motivo_inactivacion = models.CharField(max_length=12, choices=MotivoInactivacion.choices, null=True, blank=True)
    descripcion_inactivacion = models.CharField(max_length=200, null=True, blank=True)

    class Meta:
        abstract = True

    def texto_inactivacion(self) -> str:
        if self.activo or not self.motivo_inactivacion:
            return ""
        if self.motivo_inactivacion == MotivoInactivacion.OTRO:
            return f"Otro: {self.descripcion_inactivacion}"
        return self.get_motivo_inactivacion_display()


class Propietario(ConMotivoInactivacion):
    nombre_completo = models.CharField(max_length=150)
    numero_documento = models.CharField("cédula", max_length=10, unique=True)
    telefono = models.CharField("celular", max_length=10)
    correo = models.EmailField(max_length=254)
    direccion = models.CharField(max_length=200)
    fecha_registro = models.DateTimeField()

    class Meta:
        db_table = "usuarios_celdas_propietario"
        ordering = ["nombre_completo"]
        constraints = [
            models.CheckConstraint(
                condition=~Q(numero_documento__glob="*[^0-9]*")
                & Q(numero_documento__length__gte=5, numero_documento__length__lte=10),
                name="ck_propietario_cedula",
            ),
            # RN-30: celular colombiano (10 dígitos que empiezan por 3)
            models.CheckConstraint(condition=Q(telefono__glob=PATRON_CELULAR), name="ck_propietario_celular"),
            *_restricciones_inactivacion("propietario"),
        ]

    def __str__(self) -> str:
        return self.nombre_completo


class Vehiculo(ConMotivoInactivacion):
    placa = models.CharField(max_length=6, unique=True)
    tipo = models.CharField(max_length=10, choices=TipoVehiculo.choices)
    marca = models.CharField(max_length=50)
    nombre = models.CharField("nombre (línea)", max_length=50)
    modelo = models.PositiveSmallIntegerField("modelo (año)")
    color = models.CharField(max_length=30)
    propietario = models.ForeignKey(Propietario, on_delete=models.PROTECT, related_name="vehiculos")
    fecha_registro = models.DateTimeField()

    class Meta:
        db_table = "usuarios_celdas_vehiculo"
        constraints = [
            models.CheckConstraint(
                condition=Q(placa__glob=PATRONES_PLACA["CARRO"])
                | Q(placa__glob=PATRONES_PLACA["MOTO"])
                | Q(placa__glob=PATRONES_PLACA["MOTO_ANTIGUA"]),
                name="ck_vehiculo_placa",
            ),
            models.CheckConstraint(condition=Q(tipo__in=TipoVehiculo.values), name="ck_vehiculo_tipo"),
            models.CheckConstraint(condition=Q(modelo__gte=1950, modelo__lte=2100), name="ck_vehiculo_modelo"),
            *_restricciones_inactivacion("vehiculo"),
        ]

    def __str__(self) -> str:
        return self.placa

    def categoria(self) -> str:
        """Moto -> MOTO; carro o camioneta -> CARRO_CAMIONETA (RN-08)."""
        return Categoria.MOTO if self.tipo == TipoVehiculo.MOTO else Categoria.CARRO_CAMIONETA

    def descripcion(self) -> str:
        return f"{self.marca} {self.nombre} {self.modelo}, {self.color.lower()}"

    def propietario_desde(self):
        """Desde cuándo el propietario actual es dueño (DM-09): fin del último historial o fecha de registro."""
        ultimo = self.historial_propiedad.order_by("-hasta").first()
        return ultimo.hasta if ultimo else self.fecha_registro


class EstadoSolicitud(models.TextChoices):
    PENDIENTE = "PENDIENTE", "Pendiente"
    APROBADA = "APROBADA", "Aprobada"
    RECHAZADA = "RECHAZADA", "Rechazada"


class SolicitudCambioPropietario(models.Model):
    """Solicitud de cambio de propietario (RF-109, RN-33, DEC-015)."""

    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.PROTECT, related_name="solicitudes_cambio")
    propietario_actual = models.ForeignKey(Propietario, on_delete=models.PROTECT, related_name="solicitudes_como_actual")
    propietario_nuevo = models.ForeignKey(Propietario, on_delete=models.PROTECT, related_name="solicitudes_como_nuevo")
    motivo = models.TextField()
    solicitado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="solicitudes_cambio")
    fecha_solicitud = models.DateTimeField()
    estado = models.CharField(max_length=10, choices=EstadoSolicitud.choices, default=EstadoSolicitud.PENDIENTE)
    resuelto_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="solicitudes_resueltas", null=True, blank=True
    )
    fecha_resolucion = models.DateTimeField(null=True, blank=True)
    observacion = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "usuarios_celdas_solicitudcambiopropietario"
        ordering = ["-fecha_solicitud"]
        constraints = [
            models.UniqueConstraint(fields=["vehiculo"], condition=Q(estado="PENDIENTE"), name="uq_solicitud_pendiente"),
            models.CheckConstraint(condition=Q(estado__in=EstadoSolicitud.values), name="ck_solicitud_estado"),
            models.CheckConstraint(condition=~Q(propietario_nuevo=F("propietario_actual")), name="ck_solicitud_distinto"),
            models.CheckConstraint(condition=Q(motivo__trim__length__gt=0), name="ck_solicitud_motivo"),
            models.CheckConstraint(
                condition=Q(estado="PENDIENTE", resuelto_por__isnull=True, fecha_resolucion__isnull=True)
                | (~Q(estado="PENDIENTE") & Q(resuelto_por__isnull=False, fecha_resolucion__isnull=False)),
                name="ck_solicitud_resolucion",
            ),
        ]


class HistorialPropiedad(models.Model):
    """Propietarios ANTERIORES de un vehículo (DM-09). El actual está en Vehiculo.propietario."""

    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.PROTECT, related_name="historial_propiedad")
    propietario = models.ForeignKey(Propietario, on_delete=models.PROTECT, related_name="propiedades_anteriores")
    desde = models.DateTimeField()
    hasta = models.DateTimeField()

    class Meta:
        db_table = "usuarios_celdas_historialpropiedad"
        ordering = ["-hasta"]
        constraints = [models.CheckConstraint(condition=Q(hasta__gt=F("desde")), name="ck_historial_periodo")]
        indexes = [models.Index(fields=["vehiculo", "hasta"], name="idx_historial_vehiculo")]


# RN-49 (CHG-003): formato del código de celda según su tipo
PATRONES_CELDA = {Categoria.CARRO_CAMIONETA: "A-[0-9][0-9][0-9]", Categoria.MOTO: "M-[0-9][0-9]"}


class Celda(models.Model):
    """Celda del parqueadero. CHG-003: el administrador la crea y la administra (RF-103, RN-48 a RN-53)."""

    codigo = models.CharField(max_length=10, unique=True)
    tipo = models.CharField(max_length=15, choices=Categoria.choices)
    activa = models.BooleanField(default=True)
    motivo_inactivacion = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        db_table = "usuarios_celdas_celda"
        ordering = ["codigo"]
        constraints = [
            models.CheckConstraint(condition=Q(tipo__in=Categoria.values), name="ck_celda_tipo"),
            models.CheckConstraint(
                condition=Q(tipo=Categoria.CARRO_CAMIONETA, codigo__glob=PATRONES_CELDA[Categoria.CARRO_CAMIONETA])
                & ~Q(codigo="A-000")
                | Q(tipo=Categoria.MOTO, codigo__glob=PATRONES_CELDA[Categoria.MOTO]) & ~Q(codigo="M-00"),
                name="ck_celda_codigo"),
            models.CheckConstraint(condition=Q(activa=True, motivo_inactivacion__isnull=True)
                                   | Q(activa=False, motivo_inactivacion__isnull=False,
                                       motivo_inactivacion__trim__length__gt=0),
                                   name="ck_celda_motivo"),
        ]
        indexes = [models.Index(fields=["tipo", "activa"], name="idx_celda_tipo")]

    def __str__(self) -> str:
        return self.codigo

    def admite(self, vehiculo: Vehiculo) -> bool:
        """RN-08: la celda es del tipo que corresponde al vehículo."""
        return self.tipo == vehiculo.categoria()
