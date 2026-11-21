"""CalendarioCobro: funciones puras del calendario de cobro (RN-38, RN-39, DM-12; diseño 5.1).

Los vencimientos siempre se calculan desde el ancla (día de cobro), nunca desde el vencimiento
anterior; así 31/01 → 28/02 → 31/03.
"""
import calendar
from datetime import date


def sumar_meses(ancla: date, meses: int) -> date:
    """Mismo día del ancla, 'meses' meses después; si ese mes no tiene el día, el último día del mes."""
    indice = ancla.year * 12 + (ancla.month - 1) + meses
    anio, mes = divmod(indice, 12)
    mes += 1
    return date(anio, mes, min(ancla.day, calendar.monthrange(anio, mes)[1]))


def indice_de(ancla: date, vencimiento: date) -> int:
    """Número de meses entre el ancla y un vencimiento calculado desde ella."""
    return (vencimiento.year - ancla.year) * 12 + vencimiento.month - ancla.month


def siguiente_periodo(ancla: date, ultimo_vencimiento: date | None, meses: int) -> tuple[date, date]:
    """Periodo de un pago nuevo de 'meses' meses (RN-39): empieza en el último vencimiento (o en el ancla)."""
    if ultimo_vencimiento is None:
        return ancla, sumar_meses(ancla, meses)
    return ultimo_vencimiento, sumar_meses(ancla, indice_de(ancla, ultimo_vencimiento) + meses)


def meses_pendientes(ancla: date, ultimo_vencimiento: date, hoy: date) -> int:
    """Cuántos meses hay que pagar para que el vencimiento sea hoy o después (0 si está al día o vence hoy)."""
    if ultimo_vencimiento >= hoy:
        return 0
    k = indice_de(ancla, ultimo_vencimiento)
    n = 1
    while sumar_meses(ancla, k + n) < hoy:
        n += 1
    return n
