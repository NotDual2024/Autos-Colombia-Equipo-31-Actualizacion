"""Filtros de presentación de pagos."""
from django import template

register = template.Library()


@register.filter
def pesos(valor) -> str:
    """150000 -> '150 000' (separador de miles con espacio, como en los mockups)."""
    try:
        return f"{int(valor):,}".replace(",", " ")
    except (TypeError, ValueError):
        return ""


@register.filter
def etiqueta_vigencia(estado) -> str:
    """Clase de color de la etiqueta según el estado de la mensualidad."""
    return {"AL_DIA": "", "VENCE_HOY": "amarillo", "VENCIDA": "rojo"}.get(getattr(estado, "estado", ""), "gris")
