"""PlanificadorAvisos (DEC-008): ejecuta el proceso de avisos al iniciar y cada hora.

Se inicia una sola vez, y solo en el proceso que atiende el servidor:
- con `runserver` y recarga automática, Django crea dos procesos; solo el hijo
  (RUN_MAIN=true) inicia el planificador;
- con `runserver --noreload` hay un solo proceso;
- nunca se inicia en pruebas, migraciones ni otros comandos.
La restricción única de la base de datos es una segunda barrera contra duplicados.
"""
import logging
import os
import sys
import threading

from django.conf import settings

logger = logging.getLogger(__name__)

_candado = threading.Lock()
_planificador = None


def es_proceso_servidor(argv=None, entorno=None) -> bool:
    argv = sys.argv if argv is None else argv
    entorno = os.environ if entorno is None else entorno
    if len(argv) < 2 or argv[1] != "runserver":
        return False
    return "--noreload" in argv or entorno.get("RUN_MAIN") == "true"


def _ejecutar() -> None:
    from django.db import close_old_connections

    from . import services

    close_old_connections()
    try:
        services.enviar_automaticos()
    except Exception:  # el planificador nunca debe caerse (RNF-013)
        logger.exception("Error en el proceso de avisos automáticos")
    finally:
        close_old_connections()


def iniciar() -> bool:
    """Inicia el planificador si corresponde. Devuelve True si quedó iniciado."""
    global _planificador
    if not settings.AVISOS_PLANIFICADOR_ACTIVO or not es_proceso_servidor():
        return False
    with _candado:
        if _planificador is not None:
            return False
        from datetime import datetime

        from apscheduler.schedulers.background import BackgroundScheduler

        _planificador = BackgroundScheduler(timezone=settings.TIME_ZONE)
        _planificador.add_job(
            _ejecutar, "interval", minutes=settings.AVISOS_INTERVALO_MINUTOS,
            next_run_time=datetime.now(), id="avisos_vencimiento", max_instances=1, coalesce=True,
        )
        _planificador.start()
        logger.info("Planificador de avisos iniciado (cada %s minutos).", settings.AVISOS_INTERVALO_MINUTOS)
        return True
