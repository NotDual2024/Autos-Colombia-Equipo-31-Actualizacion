"""Consultas de solo lectura sobre propietarios, vehículos y celdas (RF-104, RF-108)."""
import re
from math import ceil

from django.db.models import Count, Q, QuerySet

from .models import Categoria, Celda, EstadoSolicitud, Propietario, SolicitudCambioPropietario, Vehiculo


def normalizar_placa(texto: str) -> str:
    """Mayúsculas y sin espacios ni guiones (RN-23)."""
    return re.sub(r"[\s\-]", "", (texto or "")).upper()


def vehiculo_por_placa(placa: str) -> Vehiculo | None:
    return Vehiculo.objects.select_related("propietario").filter(placa=normalizar_placa(placa)).first()


def buscar_propietarios(texto: str = "") -> QuerySet[Propietario]:
    """Por nombre o cédula (HU-014)."""
    qs = Propietario.objects.annotate(num_vehiculos=Count("vehiculos")).prefetch_related("vehiculos")
    texto = (texto or "").strip()
    if texto:
        qs = qs.filter(Q(nombre_completo__icontains=texto) | Q(numero_documento__icontains=texto))
    return qs.order_by("nombre_completo")


def buscar_vehiculos(texto: str = "", tipo: str = "") -> QuerySet[Vehiculo]:
    qs = Vehiculo.objects.select_related("propietario").order_by("placa")
    if texto:
        qs = qs.filter(Q(placa__icontains=normalizar_placa(texto)) | Q(propietario__nombre_completo__icontains=texto.strip()))
    if tipo:
        qs = qs.filter(tipo=tipo)
    return qs


def ubicacion(vehiculo: Vehiculo) -> str | None:
    """Código de la celda si el vehículo está dentro (relación inversa "estadias", sin importar entradas_salidas)."""
    abierta = vehiculo.estadias.filter(fecha_hora_salida__isnull=True).select_related("celda").first()
    return abierta.celda.codigo if abierta else None


def propietario_por_documento(documento: str) -> Propietario | None:
    return Propietario.objects.filter(numero_documento=(documento or "").strip()).first()


def solicitudes(estado: str = EstadoSolicitud.PENDIENTE) -> QuerySet[SolicitudCambioPropietario]:
    qs = SolicitudCambioPropietario.objects.select_related(
        "vehiculo", "propietario_actual", "propietario_nuevo", "solicitado_por", "resuelto_por")
    return qs.filter(estado=estado) if estado else qs


def pendientes() -> int:
    return SolicitudCambioPropietario.objects.filter(estado=EstadoSolicitud.PENDIENTE).count()


CELDAS_POR_BLOQUE = 24


def mapa_celdas(zona: str, bloque: int) -> dict:
    """Celdas de una zona en bloques de 24, con la placa de las ocupadas (RF-104, HU-018)."""
    # Se usa la relación inversa "estadias" (sin importar entradas_salidas) para no crear un ciclo
    # de dependencias entre módulos (PK-01).
    categoria = Categoria.MOTO if zona == "M" else Categoria.CARRO_CAMIONETA
    ocupacion = dict(Celda.objects.filter(tipo=categoria, estadias__isnull=False, estadias__fecha_hora_salida__isnull=True)
                     .values_list("id", "estadias__vehiculo__placa"))
    celdas = list(Celda.objects.filter(tipo=categoria, activa=True).order_by("codigo"))
    total_bloques = max(ceil(len(celdas) / CELDAS_POR_BLOQUE), 1)
    bloque = min(max(bloque, 1), total_bloques)
    inicio = (bloque - 1) * CELDAS_POR_BLOQUE
    return {
        "zona": "M" if categoria == Categoria.MOTO else "A",
        "categoria": Categoria(categoria).label,
        "celdas": [{"codigo": c.codigo, "placa": ocupacion.get(c.id)} for c in celdas[inicio:inicio + CELDAS_POR_BLOQUE]],
        "bloque": bloque, "total_bloques": total_bloques,
        "total": len(celdas), "ocupadas": len(ocupacion), "libres": len(celdas) - len(ocupacion),
    }
