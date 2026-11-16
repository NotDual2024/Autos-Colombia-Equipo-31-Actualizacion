"""Base común para las pruebas: reloj fijo y datos mínimos."""
from datetime import date, datetime, timedelta
from unittest import mock
from zoneinfo import ZoneInfo

from django.test import TestCase

from apps.cuentas.models import Rol
from apps.demo import fabricas as f

TZ = ZoneInfo("America/Bogota")
CLAVE = "ClaveSegura2026"


def fh(texto: str) -> datetime:
    return datetime.fromisoformat(texto).replace(tzinfo=TZ)


class PruebaConReloj(TestCase):
    """Fija 'ahora' en AHORA (domingo 15/11/2026 14:35, Bogotá) mediante el Reloj del sistema."""

    AHORA = fh("2026-11-15 14:35")

    def setUp(self):
        parche = mock.patch("apps.core.reloj.ahora", side_effect=lambda: self.AHORA)
        parche.start()
        self.addCleanup(parche.stop)
        self.admin = f.crear_usuario("admin", CLAVE, "Laura Castillo", Rol.ADMINISTRADOR)
        self.operador = f.crear_usuario("operador", CLAVE, "María Rodríguez")
        f.asignar_horario_24h(self.operador)  # RN-36: sin horario no puede trabajar
        f.crear_celdas(carros=3, motos=2)  # A-001..A-003, M-01..M-02
        self.prop = f.crear_propietario("Ana Gil", "1045678901", "ana.gil@correo.co")

    @property
    def hoy(self) -> date:
        return self.AHORA.date()

    def vehiculo(self, placa="ABC123", tipo="CARRO", vigente=True, propietario=None, fin=None):
        v = f.crear_vehiculo(propietario or self.prop, placa, tipo, "Chevrolet", "Spark", 2020, "Rojo")
        if fin is not None:
            f.crear_pago(v, fin, self.admin)
        elif vigente:
            f.crear_pago(v, self.hoy + timedelta(days=10), self.admin)
        return v

    def ingresar(self, usuario=None):
        self.client.force_login(usuario or self.operador)
