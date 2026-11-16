"""ServicioAvisos: vencimientos con el vehículo dentro, avisos simulados y
contacto con autoridades (RF-009 a RF-012; RN-11, RN-12, RN-17, RN-21, RN-22)."""
import logging
from dataclasses import dataclass
from datetime import date, timedelta

from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.core import reloj
from apps.core.correo import ENVIADO_SIMULADO, obtener_servicio_correo
from apps.core.errores import ErrorNegocio
from apps.entradas_salidas.models import Estadia
from apps.pagos import services as vigencia
from apps.pagos.models import Pago

from .models import AvisoCorreo, ContactoAutoridad, OrigenAviso, ResultadoEnvio

logger = logging.getLogger(__name__)

PLAZO_DIAS = 8  # RN-12
MAX_ENVIOS = 2  # RN-22: primer correo + un reenvío


class RequiereConfirmacion(ErrorNegocio):
    """El correo ya se envió una vez; el reenvío exige confirmación (RN-22)."""


@dataclass
class VencimientoDentro:
    """Fila calculada de la lista de vencidos (no se guarda)."""

    estadia: Estadia
    pago: Pago
    dias_vencido: int
    envios: int
    contactos: int

    @property
    def vehiculo(self):
        return self.estadia.vehiculo

    @property
    def fecha_limite(self) -> date:
        return self.pago.periodo_fin + timedelta(days=PLAZO_DIAS)

    @property
    def plazo_vencido(self) -> bool:
        return self.dias_vencido >= PLAZO_DIAS

    @property
    def puede_enviar(self) -> bool:
        return self.envios < MAX_ENVIOS


def _envios_exitosos(pago: Pago) -> int:
    return pago.avisos.filter(resultado=ResultadoEnvio.ENVIADO_SIMULADO).count()


def vencidos_dentro() -> list[VencimientoDentro]:
    """Vehículos con estadía abierta cuyo último pago vence hoy o ya venció (RF-009).

    Se calcula en cada consulta: si el propietario paga o el vehículo sale, deja de aparecer (RN-17).
    """
    hoy = reloj.hoy()
    filas = []
    abiertas = Estadia.objects.filter(fecha_hora_salida__isnull=True).select_related("vehiculo__propietario", "celda")
    for estadia in abiertas:
        pago = vigencia.ultimo_pago(estadia.vehiculo)
        if pago is None or pago.periodo_fin > hoy:
            continue
        filas.append(
            VencimientoDentro(
                estadia=estadia, pago=pago, dias_vencido=(hoy - pago.periodo_fin).days,
                envios=_envios_exitosos(pago), contactos=pago.contactos_autoridad.count(),
            )
        )
    return sorted(filas, key=lambda f: (-f.dias_vencido, f.vehiculo.placa))


def vencimiento_de_pago(pago_id: int) -> VencimientoDentro:
    for fila in vencidos_dentro():
        if fila.pago.id == pago_id:
            return fila
    raise ErrorNegocio("El vehículo ya no está en la lista de mensualidades vencidas.")


def construir_mensaje(fila: VencimientoDentro) -> tuple[str, str]:
    v, p = fila.vehiculo, fila.pago
    asunto = f"Mensualidad vencida - vehículo {v.placa}"
    cuerpo = (
        f"Señor(a) {v.propietario.nombre_completo}:\n"
        f"La mensualidad del vehículo {v.placa} vence el {p.periodo_fin:%d/%m/%Y}.\n"
        "Debe pagar la mensualidad para mantener el vehículo en el parqueadero.\n"
        f"Si no lo hace, el {fila.fecha_limite:%d/%m/%Y} se contactará a las autoridades para su retiro.\n"
        "Parqueadero Autos Colombia"
    )
    return asunto, cuerpo


def _enviar(fila: VencimientoDentro, numero: int, origen: str, usuario=None) -> AvisoCorreo:
    """UC-13: arma el mensaje, simula el envío y lo registra."""
    asunto, cuerpo = construir_mensaje(fila)
    destinatario = fila.vehiculo.propietario.correo
    try:
        resultado = obtener_servicio_correo().enviar(destinatario, asunto, cuerpo)
    except Exception:  # RNF-013: un fallo del correo nunca detiene el sistema
        logger.exception("Fallo del servicio de correo")
        resultado = ResultadoEnvio.FALLIDO
    exitoso = resultado == ENVIADO_SIMULADO
    return AvisoCorreo.objects.create(
        pago=fila.pago, numero_envio=numero if exitoso else None, origen=origen,
        enviado_por=usuario if origen == OrigenAviso.MANUAL else None,
        destinatario=destinatario, asunto=asunto, cuerpo=cuerpo, fecha_hora=reloj.ahora(),
        resultado=ResultadoEnvio.ENVIADO_SIMULADO if exitoso else ResultadoEnvio.FALLIDO,
    )


def enviar_automaticos() -> int:
    """UC-11: primer correo de cada vencimiento pendiente (incluye los atrasados, RN-21). Idempotente."""
    enviados = 0
    for fila in vencidos_dentro():
        if fila.envios > 0:
            continue
        try:
            with transaction.atomic():
                aviso = _enviar(fila, 1, OrigenAviso.AUTOMATICO)
        except IntegrityError:
            continue  # otro proceso ya lo envió (doble barrera con la restricción única)
        if aviso.resultado == ResultadoEnvio.ENVIADO_SIMULADO:
            enviados += 1
    if enviados:
        logger.info("Avisos automáticos enviados: %s", enviados)
    return enviados


def enviar_manual(pago_id: int, usuario, confirmar_reenvio: bool = False) -> AvisoCorreo:
    """UC-12: envío desde el botón. El reenvío pide confirmación y solo se permite uno (RN-22)."""
    fila = vencimiento_de_pago(pago_id)
    if fila.envios >= MAX_ENVIOS:
        raise ErrorNegocio("El correo de este vencimiento ya se reenvió una vez.")
    if fila.envios == 1 and not confirmar_reenvio:
        primero = fila.pago.avisos.filter(numero_envio=1).first()
        raise RequiereConfirmacion(
            f"Ya se envió un correo para este vencimiento el {timezone.localtime(primero.fecha_hora):%d/%m/%Y %H:%M}. "
            "¿Desea reenviarlo? Solo se permite un reenvío."
        )
    try:
        with transaction.atomic():
            return _enviar(fila, fila.envios + 1, OrigenAviso.MANUAL, usuario)
    except IntegrityError:
        raise ErrorNegocio("El correo ya fue enviado por otra persona. Actualiza la lista.")


def registrar_contacto(pago_id: int, administrador, observacion: str) -> ContactoAutoridad:
    """UC-14: solo administrador y solo con el plazo de 8 días vencido (RF-011, RN-12)."""
    if not administrador.es_administrador():
        raise ErrorNegocio("Acceso denegado")
    observacion = (observacion or "").strip()
    if not observacion:
        raise ErrorNegocio("La observación es obligatoria.")
    fila = vencimiento_de_pago(pago_id)
    if not fila.plazo_vencido:
        raise ErrorNegocio("El plazo de 8 días todavía no ha vencido.")
    return ContactoAutoridad.objects.create(
        pago=fila.pago, fecha_hora=reloj.ahora(), registrado_por=administrador, observacion=observacion
    )

