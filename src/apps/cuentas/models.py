"""Usuarios del sistema (RNF-001, RNF-002, RF-106) y horario provisional (RF-107)."""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q


class Rol(models.TextChoices):
    ADMINISTRADOR = "ADMINISTRADOR", "Administrador"
    OPERADOR = "OPERADOR", "Operador"


class Usuario(AbstractUser):
    """Usuario con rol. Nunca se borra: se desactiva con is_active (RN-07)."""

    rol = models.CharField(max_length=15, choices=Rol.choices, default=Rol.OPERADOR)

    class Meta:
        db_table = "cuentas_usuario"
        constraints = [
            models.CheckConstraint(condition=Q(rol__in=Rol.values), name="ck_usuario_rol"),
        ]

    def es_administrador(self) -> bool:
        return self.rol == Rol.ADMINISTRADOR

    def nombre_completo(self) -> str:
        return self.get_full_name() or self.username

    def iniciales(self) -> str:
        partes = self.nombre_completo().split()
        return "".join(p[0] for p in partes[:2]).upper()


class HorarioOperador(models.Model):
    """PROVISIONAL (iteración 2, RF-107): sin pantallas en la iteración 1."""

    operador = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name="horarios")
    dia_semana = models.PositiveSmallIntegerField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()

    class Meta:
        db_table = "cuentas_horariooperador"
        constraints = [
            models.CheckConstraint(condition=Q(dia_semana__gte=1, dia_semana__lte=7), name="ck_horario_dia"),
            models.CheckConstraint(condition=~Q(hora_inicio=models.F("hora_fin")), name="ck_horario_horas"),
        ]
