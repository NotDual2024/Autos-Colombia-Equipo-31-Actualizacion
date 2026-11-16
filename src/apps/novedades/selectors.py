"""ConsultasNovedades (RF-008)."""
from datetime import date, datetime, time

from django.db.models import Prefetch, QuerySet
from django.utils import timezone

from .models import Novedad, NovedadEstadia

_VINCULOS = Prefetch(
    "vinculos", queryset=NovedadEstadia.objects.select_related("estadia__vehiculo", "estadia__celda")
)


def buscar(placa: str | None = None, tipo: str | None = None, desde: date | None = None, hasta: date | None = None) -> QuerySet[Novedad]:
    """De la más reciente a la más antigua; una novedad con varios vehículos aparece por cualquiera."""
    qs = Novedad.objects.select_related("registrado_por").prefetch_related(_VINCULOS).order_by("-fecha_hora_ocurrencia", "-id")
    if placa:
        qs = qs.filter(vinculos__estadia__vehiculo__placa__icontains=placa).distinct()
    if tipo:
        qs = qs.filter(tipo=tipo)
    zona = timezone.get_current_timezone()
    if desde:
        qs = qs.filter(fecha_hora_ocurrencia__gte=datetime.combine(desde, time.min, tzinfo=zona))
    if hasta:
        qs = qs.filter(fecha_hora_ocurrencia__lte=datetime.combine(hasta, time.max, tzinfo=zona))
    return qs


def de_estadia(estadia) -> QuerySet[Novedad]:
    """Novedades vinculadas a una estadía (pantallas de salida e historial)."""
    return buscar().filter(vinculos__estadia=estadia)
