"""Usuarios del sistema (RNF-001, RNF-002, RF-106), horarios (RF-107) y autorizaciones (RF-110)."""
from datetime import date, datetime, time, timedelta

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import F, Q
from django.utils import timezone

MINUTOS_DIA = 24 * 60
MINUTOS_SEMANA = 7 * MINUTOS_DIA
DIAS = {1: "Lunes", 2: "Martes", 3: "Miércoles", 4: "Jueves", 5: "Viernes", 6: "Sábado", 7: "Domingo"}


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


def _minutos(t: time) -> int:
    return t.hour * 60 + t.minute


class HorarioOperador(models.Model):
    """Franja de trabajo de un día de la semana (DEC-014). dia_semana: 1 = lunes ... 7 = domingo.

    Si hora_fin <= hora_inicio, la franja cruza la medianoche y termina al día siguiente (RN-36).
    """

    operador = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name="horarios")
    dia_semana = models.PositiveSmallIntegerField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()

    class Meta:
        db_table = "cuentas_horariooperador"
        ordering = ["dia_semana", "hora_inicio"]
        constraints = [
            models.CheckConstraint(condition=Q(dia_semana__gte=1, dia_semana__lte=7), name="ck_horario_dia"),
            models.CheckConstraint(condition=~Q(hora_inicio=F("hora_fin")), name="ck_horario_horas"),
        ]
        indexes = [models.Index(fields=["operador", "dia_semana"], name="idx_horario_operador_dia")]

    def __str__(self) -> str:
        return f"{DIAS[self.dia_semana]} {self.hora_inicio:%H:%M} - {self.hora_fin:%H:%M}"

    @property
    def nombre_dia(self) -> str:
        return DIAS[self.dia_semana]

    def cruza_medianoche(self) -> bool:
        return self.hora_fin <= self.hora_inicio

    def _intervalo_semana(self) -> tuple[int, int]:
        """Inicio y fin en minutos contados desde el lunes 00:00 (el fin puede pasar del domingo)."""
        inicio = (self.dia_semana - 1) * MINUTOS_DIA + _minutos(self.hora_inicio)
        duracion = (_minutos(self.hora_fin) - _minutos(self.hora_inicio)) % MINUTOS_DIA or MINUTOS_DIA
        return inicio, inicio + duracion

    def se_cruza_con(self, otra: "HorarioOperador") -> bool:
        """RN-37: dos franjas del mismo operador no pueden solaparse (se considera la semana circular)."""
        a1, a2 = self._intervalo_semana()
        b1, b2 = otra._intervalo_semana()
        for desplazamiento in (-MINUTOS_SEMANA, 0, MINUTOS_SEMANA):
            if a1 < b2 + desplazamiento and b1 + desplazamiento < a2:
                return True
        return False

    def _inicio_vigente(self, momento: datetime) -> datetime | None:
        """Fecha y hora de inicio de la ocurrencia de esta franja que cubre el momento, si la hay."""
        local = timezone.localtime(momento)
        for dias_atras in (0, 1):
            dia: date = local.date() - timedelta(days=dias_atras)
            if dia.isoweekday() != self.dia_semana:
                continue
            inicio = timezone.make_aware(datetime.combine(dia, self.hora_inicio))
            fin = timezone.make_aware(datetime.combine(dia + timedelta(days=1 if self.cruza_medianoche() else 0), self.hora_fin))
            if inicio <= local < fin:
                return inicio
        return None

    def cubre(self, momento: datetime) -> bool:
        return self._inicio_vigente(momento) is not None

    def fin_en(self, momento: datetime) -> datetime | None:
        """Fin de la ocurrencia de esta franja que cubre el momento."""
        inicio = self._inicio_vigente(momento)
        if inicio is None:
            return None
        dias = 1 if self.cruza_medianoche() else 0
        return timezone.make_aware(datetime.combine(timezone.localtime(inicio).date() + timedelta(days=dias), self.hora_fin))


class AutorizacionFueraTurno(models.Model):
    """Autorización del administrador para ingresar fuera del turno (RF-110, RN-32)."""

    operador = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name="autorizaciones")
    autorizado_por = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name="autorizaciones_otorgadas")
    motivo = models.TextField()
    desde = models.DateTimeField()
    hasta = models.DateTimeField()
    fecha_registro = models.DateTimeField()

    class Meta:
        db_table = "cuentas_autorizacionfueraturno"
        ordering = ["-desde"]
        constraints = [
            models.CheckConstraint(condition=Q(hasta__gt=F("desde")), name="ck_autorizacion_periodo"),
            models.CheckConstraint(condition=~Q(operador=F("autorizado_por")), name="ck_autorizacion_otro_usuario"),
            models.CheckConstraint(condition=Q(motivo__trim__length__gt=0), name="ck_autorizacion_motivo"),
        ]
        indexes = [models.Index(fields=["operador", "hasta"], name="idx_autorizacion_operador")]

    def vigente(self, momento: datetime) -> bool:
        return self.desde <= momento < self.hasta
