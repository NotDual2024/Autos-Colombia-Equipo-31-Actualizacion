"""ServicioVigencia: vigencia de la mensualidad (RF-002, RF-009, RN-03, RN-10)."""
from datetime import date

from apps.usuarios_celdas.models import Vehiculo

from .models import Pago


def ultimo_pago(vehiculo: Vehiculo) -> Pago | None:
    """Pago con el periodo que termina más tarde (define el vencimiento actual)."""
    return vehiculo.pagos.order_by("-periodo_fin", "-id").first()


def esta_vigente(vehiculo: Vehiculo, fecha: date) -> bool:
    """La mensualidad está vigente si algún pago cubre la fecha (incluido el día de vencimiento)."""
    return vehiculo.pagos.filter(periodo_inicio__lte=fecha, periodo_fin__gte=fecha).exists()
