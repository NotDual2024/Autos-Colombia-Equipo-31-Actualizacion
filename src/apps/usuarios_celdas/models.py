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


class Propietario(models.Model):
    nombre_completo = models.CharField(max_length=150)
    numero_documento = models.CharField("cédula", max_length=10, unique=True)
    telefono = models.CharField("celular", max_length=10)
    correo = models.EmailField(max_length=254)
    direccion = models.CharField(max_length=200)
    activo = models.BooleanField(default=True)
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
        ]

    def __str__(self) -> str:
        return self.nombre_completo


class Vehiculo(models.Model):
    placa = models.CharField(max_length=6, unique=True)
    tipo = models.CharField(max_length=10, choices=TipoVehiculo.choices)
    marca = models.CharField(max_length=50)
    nombre = models.CharField("nombre (línea)", max_length=50)
    modelo = models.PositiveSmallIntegerField("modelo (año)")
    color = models.CharField(max_length=30)
    propietario = models.ForeignKey(Propietario, on_delete=models.PROTECT, related_name="vehiculos")
    activo = models.BooleanField(default=True)
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


class Celda(models.Model):
    codigo = models.CharField(max_length=10, unique=True)
    tipo = models.CharField(max_length=15, choices=Categoria.choices)
    activa = models.BooleanField(default=True)

    class Meta:
        db_table = "usuarios_celdas_celda"
        ordering = ["codigo"]
        constraints = [
            models.CheckConstraint(condition=Q(tipo__in=Categoria.values), name="ck_celda_tipo"),
        ]
        indexes = [models.Index(fields=["tipo", "activa"], name="idx_celda_tipo")]

    def __str__(self) -> str:
        return self.codigo

    def admite(self, vehiculo: Vehiculo) -> bool:
        """RN-08: la celda es del tipo que corresponde al vehículo."""
        return self.tipo == vehiculo.categoria()
