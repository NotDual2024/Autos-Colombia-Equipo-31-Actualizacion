"""ServicioPagos y ServicioConfirmacion (RF-201, RF-206, RN-38 a RN-47; diseño iteración 3, sección 5.2)."""
from dataclasses import dataclass, field
from datetime import date

from django.db import IntegrityError, transaction
from django.db.models import Max

from apps.bitacora import services as bitacora
from apps.bitacora.models import Accion, Entidad
from apps.core import reloj
from apps.core.correo import obtener_servicio_correo
from apps.core.errores import ErrorNegocio
from apps.usuarios_celdas import services as clientes
from apps.usuarios_celdas.models import MotivoInactivacion, Vehiculo

from . import calendario, services as vigencia, tarifas
from .models import CorreoConfirmacion, Descuento, EstadoPago, MedioPago, Pago, valor_descuento

MESES_MAXIMO = 12  # RN-40


def pesos(valor: int) -> str:
    return f"{valor:,}".replace(",", " ") + " COP"


@dataclass(frozen=True)
class ResumenPago:
    periodo_inicio: date
    periodo_fin: date
    meses: int
    tarifa_unitaria: int
    valor_bruto: int
    porcentaje_descuento: int | None
    valor_descuento: int
    valor: int
    descuento: Descuento | None = None


@dataclass
class ResultadoPago:
    pago: Pago
    correo_enviado: bool
    reactivados: list[str] = field(default_factory=list)
    advertencias: list[str] = field(default_factory=list)


def _meses_validos(meses) -> int:
    try:
        meses = int(meses)
    except (TypeError, ValueError):
        raise ErrorNegocio("El número de meses debe estar entre 1 y 12.")
    if not 1 <= meses <= MESES_MAXIMO:
        raise ErrorNegocio("El número de meses debe estar entre 1 y 12.")
    return meses


def _descuento_valido(descuento_id) -> Descuento | None:
    if descuento_id in (None, "", "0", 0):
        return None
    descuento = Descuento.objects.filter(pk=descuento_id).first()
    if descuento is None or not descuento.habilitado:
        raise ErrorNegocio("El descuento elegido ya no está habilitado.")
    return descuento


def preparar(vehiculo: Vehiculo, meses, descuento_id=None, *, corrige: Pago | None = None) -> ResumenPago:
    """Calcula el periodo y el valor sin guardar nada (M-26). Si 'corrige', el periodo empieza donde empezaba ese pago."""
    meses = _meses_validos(meses)
    descuento = _descuento_valido(descuento_id)
    hoy = reloj.hoy()
    if corrige is not None:
        ancla = vigencia.ancla(vehiculo) or corrige.periodo_inicio
        inicio = corrige.periodo_inicio
        fin = calendario.sumar_meses(ancla, calendario.indice_de(ancla, inicio) + meses)
    else:
        ultimo = vigencia.ultimo_pago(vehiculo)
        ancla = vigencia.ancla(vehiculo) or hoy
        inicio, fin = calendario.siguiente_periodo(ancla, ultimo.periodo_fin if ultimo else None, meses)
    tarifa = tarifas.vigente(vehiculo.categoria(), hoy).valor
    bruto = tarifa * meses
    porcentaje = descuento.porcentaje if descuento else None
    rebaja = valor_descuento(bruto, porcentaje)
    return ResumenPago(inicio, fin, meses, tarifa, bruto, porcentaje, rebaja, bruto - rebaja, descuento)


def _siguiente_factura() -> int:
    return (Pago.objects.aggregate(m=Max("numero_factura"))["m"] or 0) + 1


def _medio_valido(medio: str) -> str:
    if medio not in MedioPago.values:
        raise ErrorNegocio("Elige el medio de pago: efectivo, transferencia o tarjeta.")
    return medio


def _guardar(vehiculo: Vehiculo, resumen: ResumenPago, medio: str, usuario, corrige: Pago | None = None) -> Pago:
    try:
        with transaction.atomic():
            return Pago.objects.create(
                vehiculo=vehiculo, periodo_inicio=resumen.periodo_inicio, periodo_fin=resumen.periodo_fin,
                meses=resumen.meses, tarifa_unitaria=resumen.tarifa_unitaria, valor_bruto=resumen.valor_bruto,
                descuento=resumen.descuento, porcentaje_descuento=resumen.porcentaje_descuento, valor=resumen.valor,
                medio=medio, numero_factura=_siguiente_factura(), fecha_pago=reloj.ahora(), registrado_por=usuario,
                corrige_a=corrige,
            )
    except IntegrityError:
        raise ErrorNegocio("El pago ya fue registrado; revisa el historial de pagos del vehículo.")


def _reactivar_y_advertir(vehiculo: Vehiculo, usuario, resultado: ResultadoPago) -> None:
    """UC-35 / RN-46: solo si el pago deja el vehículo al día."""
    estado = vigencia.estado(vehiculo, reloj.hoy())
    if not estado.puede_entrar:
        resultado.advertencias.append(
            f"El vehículo sigue con la mensualidad vencida: debe {estado.meses_pendientes} "
            f"mes{'es' if estado.meses_pendientes != 1 else ''} más para quedar al día.")
        return
    for registro, nombre in ((vehiculo, f"el vehículo {vehiculo.placa}"),
                             (vehiculo.propietario, f"el propietario {vehiculo.propietario.nombre_completo}")):
        if clientes.reactivar_por_pago(registro, usuario):
            resultado.reactivados.append(nombre)
        elif not registro.activo and registro.motivo_inactivacion == MotivoInactivacion.OTRO:
            resultado.advertencias.append(
                f"{nombre[0].upper()}{nombre[1:]} está inactivo por otro motivo ({registro.descripcion_inactivacion}): "
                "debe activarse a mano.")


def enviar_confirmacion(pago: Pago) -> CorreoConfirmacion:
    """UC-36 / RN-47: correo simulado al propietario. Un fallo no deshace el pago."""
    v = pago.vehiculo
    propietario = v.propietario
    asunto = f"Pago registrado - vehículo {v.placa} - factura {pago.numero_factura_texto}"
    cuerpo = (
        f"Señor(a) {propietario.nombre_completo}:\n"
        f"Registramos el pago de la mensualidad del vehículo {v.placa}.\n"
        f"Periodo: {pago.periodo_inicio:%d/%m/%Y} a {pago.periodo_fin:%d/%m/%Y} ({pago.meses} "
        f"mes{'es' if pago.meses != 1 else ''}).\n"
        f"Valor: {pesos(pago.valor)} ({pago.get_medio_display().lower()}). Factura N.º {pago.numero_factura_texto}.\n"
        "Simulación - sin validez fiscal.\n"
        "Parqueadero Autos Colombia"
    )
    resultado = obtener_servicio_correo().enviar(propietario.correo, asunto, cuerpo)
    return CorreoConfirmacion.objects.create(pago=pago, destinatario=propietario.correo, asunto=asunto, cuerpo=cuerpo,
                                             fecha_hora=reloj.ahora(), resultado=resultado)


def _completar(pago: Pago, usuario) -> ResultadoPago:
    correo = enviar_confirmacion(pago)
    resultado = ResultadoPago(pago=pago, correo_enviado=correo.resultado == "ENVIADO_SIMULADO")
    _reactivar_y_advertir(pago.vehiculo, usuario, resultado)
    return resultado


@transaction.atomic
def registrar(vehiculo: Vehiculo, meses, medio: str, descuento_id, usuario) -> ResultadoPago:
    """UC-30 / HU-024. El resumen se calcula de nuevo en el servidor (no se confía en la pantalla)."""
    medio = _medio_valido(medio)
    resumen = preparar(vehiculo, meses, descuento_id)
    pago = _guardar(vehiculo, resumen, medio, usuario)
    texto_desc = f", descuento {resumen.porcentaje_descuento} %" if resumen.porcentaje_descuento else ""
    bitacora.registrar(usuario, Accion.CREAR, Entidad.PAGO, pago.pk,
                       f"Registró el pago de {vehiculo.placa}: {pago.meses} mes(es), {pesos(pago.valor)}{texto_desc} "
                       f"(factura {pago.numero_factura_texto})")
    return _completar(pago, usuario)


def es_ultimo(pago: Pago) -> bool:
    ultimo = vigencia.ultimo_pago(pago.vehiculo)
    return ultimo is not None and ultimo.pk == pago.pk


@transaction.atomic
def corregir(pago_id: int, motivo: str, meses, medio: str, descuento_id, usuario) -> ResultadoPago:
    """UC-34 / HU-029 (RN-44, DM-13): marca el pago como corregido y registra el correcto, que lo apunta."""
    pago = Pago.objects.select_for_update().select_related("vehiculo__propietario").filter(pk=pago_id).first()
    if pago is None:
        raise ErrorNegocio("El pago no existe.")
    if pago.estado == EstadoPago.CORREGIDO:
        raise ErrorNegocio("Este pago ya fue corregido; corrige el pago que lo reemplazó.")
    ahora = reloj.ahora()
    if not pago.corregible_por(usuario, ahora):
        raise ErrorNegocio("Este pago solo lo puede corregir el administrador")
    if not es_ultimo(pago):
        raise ErrorNegocio("Solo se puede corregir el último pago registrado del vehículo. Corrige primero los posteriores.")
    motivo = " ".join((motivo or "").split())
    if not motivo:
        raise ErrorNegocio("Escribe el motivo de la corrección.")
    medio = _medio_valido(medio)
    vehiculo = pago.vehiculo
    resumen = preparar(vehiculo, meses, descuento_id, corrige=pago)
    pago.estado, pago.motivo_correccion, pago.corregido_por, pago.fecha_correccion = EstadoPago.CORREGIDO, motivo, usuario, ahora
    pago.save(update_fields=["estado", "motivo_correccion", "corregido_por", "fecha_correccion"])
    nuevo = _guardar(vehiculo, resumen, medio, usuario, corrige=pago)
    bitacora.registrar(usuario, Accion.CORREGIR_PAGO, Entidad.PAGO, pago.pk,
                       f"Corrigió el pago de {vehiculo.placa} (factura {pago.numero_factura_texto} → "
                       f"{nuevo.numero_factura_texto})",
                       {"motivo": ["", motivo], "meses": [str(pago.meses), str(nuevo.meses)],
                        "valor": [pesos(pago.valor), pesos(nuevo.valor)], "medio": [pago.get_medio_display(), nuevo.get_medio_display()]})
    return _completar(nuevo, usuario)
