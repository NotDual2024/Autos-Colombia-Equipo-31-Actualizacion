"""ServicioNovedades: registro de novedades (RF-007, RN-06, RN-14 a RN-16, RN-18)."""
from datetime import datetime

from django.db import transaction

from apps.core import reloj
from apps.core.errores import ErrorNegocio
from apps.entradas_salidas import selectors as consultas_estadias
from apps.usuarios_celdas.selectors import normalizar_placa, vehiculo_por_placa

from .models import Novedad, NovedadEstadia, TipoNovedad


def separar_placas(texto: str) -> list[str]:
    """'ABC123, def456 ABC123' -> ['ABC123', 'DEF456'] (sin repetir, en orden)."""
    placas: list[str] = []
    for parte in (texto or "").replace(";", ",").replace("\n", ",").split(","):
        for trozo in parte.split():
            placa = normalizar_placa(trozo)
            if placa and placa not in placas:
                placas.append(placa)
    return placas


@transaction.atomic
def registrar(placas: list[str], tipo: str, ocurrencia: datetime, descripcion: str, usuario) -> Novedad:
    placas = [normalizar_placa(p) for p in placas if normalizar_placa(p)]
    placas = list(dict.fromkeys(placas))
    if not placas:
        raise ErrorNegocio("Indica al menos un vehículo involucrado.")
    if tipo not in TipoNovedad.values:
        raise ErrorNegocio("Selecciona un tipo de novedad válido.")
    descripcion = (descripcion or "").strip()
    if not descripcion:
        raise ErrorNegocio("La descripción es obligatoria. Completa este campo para guardar.")
    ahora = reloj.ahora()
    if ocurrencia > ahora:
        raise ErrorNegocio("La fecha y hora del hecho no puede ser posterior a la actual.")

    estadias = []
    no_registrados, no_presentes = [], []
    for placa in placas:
        vehiculo = vehiculo_por_placa(placa)
        if vehiculo is None:
            no_registrados.append(placa)
            continue
        estadia = consultas_estadias.estadia_en(vehiculo, ocurrencia)
        if estadia is None:
            no_presentes.append(placa)
        else:
            estadias.append(estadia)
    if no_registrados:
        raise ErrorNegocio(f"Vehículo no registrado: {', '.join(no_registrados)}.")
    if no_presentes:
        verbo = "no estaba" if len(no_presentes) == 1 else "no estaban"
        raise ErrorNegocio(f"{', '.join(no_presentes)} {verbo} dentro del parqueadero a la hora indicada.")

    novedad = Novedad.objects.create(
        tipo=tipo, descripcion=descripcion, fecha_hora_ocurrencia=ocurrencia,
        fecha_hora_registro=ahora, registrado_por=usuario,
    )
    NovedadEstadia.objects.bulk_create([NovedadEstadia(novedad=novedad, estadia=e) for e in estadias])
    return novedad
