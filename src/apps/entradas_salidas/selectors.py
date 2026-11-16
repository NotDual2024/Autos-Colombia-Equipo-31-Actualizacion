"""ConsultasEstadias: consultas de solo lectura (RF-005, RF-006, RF-007)."""
from datetime import date, datetime, time

from django.db.models import Count, Q, QuerySet
from django.utils import timezone

from apps.usuarios_celdas.models import Categoria, Celda, TipoVehiculo, Vehiculo

from .models import Estadia

ESTADIAS = Estadia.objects.select_related("vehiculo", "vehiculo__propietario", "celda", "usuario_entrada", "usuario_salida")


def estadia_abierta(vehiculo: Vehiculo) -> Estadia | None:
    return ESTADIAS.filter(vehiculo=vehiculo, fecha_hora_salida__isnull=True).first()


def vehiculos_dentro(tipo: str | None = None, placa: str | None = None) -> QuerySet[Estadia]:
    qs = ESTADIAS.filter(fecha_hora_salida__isnull=True).order_by("fecha_hora_entrada")
    if tipo:
        qs = qs.filter(vehiculo__tipo=tipo)
    if placa:
        qs = qs.filter(vehiculo__placa__icontains=placa)
    return qs


def ocupacion_por_categoria() -> dict[str, dict[str, int]]:
    """Celdas ocupadas, totales y porcentaje por categoría (RF-005)."""
    resultado = {}
    ocupadas_ids = set(Estadia.objects.filter(fecha_hora_salida__isnull=True).values_list("celda_id", flat=True))
    for categoria in Categoria.values:
        ids = list(Celda.objects.filter(tipo=categoria, activa=True).values_list("id", flat=True))
        total = len(ids)
        ocupadas = sum(1 for i in ids if i in ocupadas_ids)
        resultado[categoria] = {
            "total": total,
            "ocupadas": ocupadas,
            "disponibles": total - ocupadas,
            "porcentaje": round(ocupadas * 100 / total) if total else 0,
        }
    return resultado


def ocupacion_celda(codigo: str) -> tuple[Celda | None, Estadia | None]:
    """Celda consultada y su estadía abierta, si está ocupada (RF-005)."""
    celda = Celda.objects.filter(codigo__iexact=(codigo or "").strip()).first()
    if celda is None:
        return None, None
    return celda, ESTADIAS.filter(celda=celda, fecha_hora_salida__isnull=True).first()


def celdas_de_categoria(categoria: str) -> list[dict]:
    """Todas las celdas activas de una categoría con su estado (para la cuadrícula de RF-003)."""
    ocupadas = set(Estadia.objects.filter(fecha_hora_salida__isnull=True).values_list("celda_id", flat=True))
    return [
        {"codigo": c.codigo, "ocupada": c.id in ocupadas}
        for c in Celda.objects.filter(tipo=categoria, activa=True).order_by("codigo")
    ]


def historial(placa: str | None = None, desde: date | None = None, hasta: date | None = None) -> QuerySet[Estadia]:
    """Movimientos filtrados por placa y por fecha de ingreso (RF-006)."""
    qs = ESTADIAS.annotate(num_novedades=Count("vinculos_novedad")).order_by("-fecha_hora_entrada")
    if placa:
        qs = qs.filter(vehiculo__placa__icontains=placa)
    zona = timezone.get_current_timezone()
    if desde:
        qs = qs.filter(fecha_hora_entrada__gte=datetime.combine(desde, time.min, tzinfo=zona))
    if hasta:
        qs = qs.filter(fecha_hora_entrada__lte=datetime.combine(hasta, time.max, tzinfo=zona))
    return qs


def estadia_en(vehiculo: Vehiculo, momento: datetime) -> Estadia | None:
    """Estadía del vehículo que incluye ese momento (RF-007, RN-16)."""
    return (
        Estadia.objects.filter(vehiculo=vehiculo, fecha_hora_entrada__lte=momento)
        .filter(Q(fecha_hora_salida__isnull=True) | Q(fecha_hora_salida__gte=momento))
        .first()
    )


TIPOS_VEHICULO = TipoVehiculo.choices
