"""ConsultasPagos: historiales, factura, por vencer e ingresos (RF-203, RF-207, RF-209). Solo lectura."""
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta

from django.db.models import Count, Sum
from django.utils import timezone

from apps.usuarios_celdas.models import Categoria, Propietario, Vehiculo

from . import services as vigencia
from .models import EstadoPago, MedioPago, Pago

DIAS_POR_VENCER = 5  # RF-207


def _con_relaciones(qs):
    return qs.select_related("vehiculo__propietario", "registrado_por", "descuento", "corregido_por", "reemplazo")


def historial_vehiculo(vehiculo: Vehiculo):
    return _con_relaciones(vehiculo.pagos.all()).order_by("-fecha_pago", "-id")


def historial_propietario(propietario: Propietario):
    return _con_relaciones(Pago.objects.filter(vehiculo__propietario=propietario)).order_by("-fecha_pago", "-id")


def factura(numero: int) -> Pago | None:
    return _con_relaciones(Pago.objects.filter(numero_factura=numero)).first()


@dataclass
class FilaPorVencer:
    vehiculo: Vehiculo
    vencimiento: date
    dias: int


def por_vencer(hoy: date, dias: int = DIAS_POR_VENCER) -> list[FilaPorVencer]:
    """HU-030: vehículos activos cuya mensualidad vence hoy o en los próximos 'dias' días."""
    limite = hoy + timedelta(days=dias)
    filas = []
    for v in Vehiculo.objects.filter(activo=True).select_related("propietario"):
        ultimo = vigencia.ultimo_pago(v)
        if ultimo and hoy <= ultimo.periodo_fin <= limite:
            filas.append(FilaPorVencer(v, ultimo.periodo_fin, (ultimo.periodo_fin - hoy).days))
    return sorted(filas, key=lambda f: (f.vencimiento, f.vehiculo.placa))


@dataclass
class InformeIngresos:
    anio: int
    mes: int
    total: int = 0
    cantidad: int = 0
    por_tipo: list[dict] = field(default_factory=list)
    por_medio: list[dict] = field(default_factory=list)


def ingresos(anio: int, mes: int) -> InformeIngresos:
    """HU-032: por fecha de pago, sin pagos corregidos, por tipo de vehículo y por medio de pago."""
    zona = timezone.get_current_timezone()
    inicio = datetime.combine(date(anio, mes, 1), time.min, tzinfo=zona)
    siguiente = date(anio + (mes == 12), mes % 12 + 1, 1)
    fin = datetime.combine(siguiente, time.min, tzinfo=zona)
    qs = Pago.objects.filter(estado=EstadoPago.REGISTRADO, fecha_pago__gte=inicio, fecha_pago__lt=fin)
    informe = InformeIngresos(anio, mes)
    totales = qs.aggregate(total=Sum("valor"), cantidad=Count("id"))
    informe.total, informe.cantidad = totales["total"] or 0, totales["cantidad"]
    motos = qs.filter(vehiculo__tipo="MOTO").aggregate(total=Sum("valor"), cantidad=Count("id"))
    carros = qs.exclude(vehiculo__tipo="MOTO").aggregate(total=Sum("valor"), cantidad=Count("id"))
    informe.por_tipo = [
        {"nombre": Categoria.CARRO_CAMIONETA.label, "cantidad": carros["cantidad"], "total": carros["total"] or 0},
        {"nombre": Categoria.MOTO.label, "cantidad": motos["cantidad"], "total": motos["total"] or 0},
    ]
    por_medio = {m["medio"]: m for m in qs.values("medio").annotate(total=Sum("valor"), cantidad=Count("id"))}
    informe.por_medio = [
        {"nombre": etiqueta, "cantidad": por_medio.get(valor, {}).get("cantidad", 0), "total": por_medio.get(valor, {}).get("total") or 0}
        for valor, etiqueta in MedioPago.choices
    ]
    return informe
