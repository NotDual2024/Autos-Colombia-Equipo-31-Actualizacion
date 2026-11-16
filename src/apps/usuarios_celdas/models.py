"""Propietarios, vehículos y celdas (modelo de datos v1.1; pantallas en la iteración 2)."""
from django.db import models
from django.db.models import Q


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


class Propietario(models.Model):
    nombre_completo = models.CharField(max_length=150)
    numero_documento = models.CharField("cédula", max_length=10, unique=True)
    telefono = models.CharField(max_length=20)
    correo = models.EmailField(max_length=254)
    direccion = models.CharField(max_length=200)
    activo = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField()

    class Meta:
        db_table = "usuarios_celdas_propietario"
        constraints = [
            models.CheckConstraint(
                condition=~Q(numero_documento__glob="*[^0-9]*")
                & Q(numero_documento__length__gte=5, numero_documento__length__lte=10),
                name="ck_propietario_cedula",
            ),
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
