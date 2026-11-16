"""Servicio de correo (DEC-007).

ServicioCorreo es la interfaz; ServicioCorreoSimulado es la única implementación
de esta versión: no contacta ningún servidor. Para conectar un correo real en el
futuro basta con otra implementación (RNF-012).
"""
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

ENVIADO_SIMULADO = "ENVIADO_SIMULADO"
FALLIDO = "FALLIDO"


class ServicioCorreo(ABC):
    @abstractmethod
    def enviar(self, destinatario: str, asunto: str, cuerpo: str) -> str:
        """Devuelve ENVIADO_SIMULADO o FALLIDO. No debe lanzar excepciones."""


class ServicioCorreoSimulado(ServicioCorreo):
    """Simula el envío: solo deja constancia en el log."""

    def enviar(self, destinatario: str, asunto: str, cuerpo: str) -> str:
        logger.info("Correo simulado a %s: %s", destinatario, asunto)
        return ENVIADO_SIMULADO


_servicio_actual: ServicioCorreo = ServicioCorreoSimulado()


def obtener_servicio_correo() -> ServicioCorreo:
    return _servicio_actual


def usar_servicio_correo(servicio: ServicioCorreo) -> None:
    """Permite sustituir la implementación (por ejemplo, en pruebas)."""
    global _servicio_actual
    _servicio_actual = servicio
