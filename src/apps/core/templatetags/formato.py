"""Filtros de presentación comunes."""
from datetime import datetime

from django import template

from apps.core import reloj

register = template.Library()


@register.filter
def duracion(inicio: datetime, fin: datetime | None = None) -> str:
    """'5 h 25 min' entre inicio y fin (o ahora si fin es None)."""
    if inicio is None:
        return ""
    fin = fin or reloj.ahora()
    minutos = max(int((fin - inicio).total_seconds() // 60), 0)
    dias, resto = divmod(minutos, 24 * 60)
    horas, mins = divmod(resto, 60)
    if dias:
        return f"{dias} d {horas} h"
    if horas:
        return f"{horas} h {mins} min"
    return f"{mins} min"


@register.filter
def get_item(diccionario, clave):
    """{{ dic|get_item:clave }}: valor de un diccionario por una clave variable."""
    try:
        return diccionario.get(clave)
    except AttributeError:
        return None
