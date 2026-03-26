"""Cliente REST para la API pública de SAMAI.

Responsabilidad única: comunicarse con la API de SAMAI y devolver datos tipados.
No tiene estado, no habla con DynamoDB, no envía correos.
"""
from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

import requests

from models import Actuacion

logger = logging.getLogger(__name__)

BASE_URL = "https://samaicore.consejodeestado.gov.co/api"
TIMEOUT = 15  # seconds — API Gateway corta en 29s; 15s deja margen para reintentos
TIMEOUT_BUSQUEDA = 10  # timeout reducido para búsqueda paralela de corporación
MODO = "2"  # consulta pública

# Consejo de Estado + 27 Tribunales Administrativos de Colombia (de WEstados.aspx).
# Se usan como candidatos cuando la corporacion extraída del radicado no retorna datos.
# Los Juzgados Administrativos no se incluyen porque su código = primeros 7 dígitos del radicado.
_TRIBUNALES_Y_CE: list[str] = [
    "1100103",  # Consejo de Estado
    "0500123",  # Tribunal Administrativo de Antioquia
    "8100123",  # Tribunal Administrativo de Arauca
    "0800123",  # Tribunal Administrativo del Atlántico
    "1300123",  # Tribunal Administrativo de Bolívar
    "1500123",  # Tribunal Administrativo de Boyacá
    "1700123",  # Tribunal Administrativo de Caldas
    "1800123",  # Tribunal Administrativo del Caquetá
    "8500123",  # Tribunal Administrativo del Casanare
    "1900123",  # Tribunal Administrativo del Cauca
    "2000123",  # Tribunal Administrativo del Cesar
    "2700123",  # Tribunal Administrativo del Chocó
    "2300123",  # Tribunal Administrativo de Córdoba
    "2500023",  # Tribunal Administrativo de Cundinamarca (código especial)
    "4100123",  # Tribunal Administrativo del Huila
    "4400123",  # Tribunal Administrativo de la Guajira
    "4700123",  # Tribunal Administrativo del Magdalena
    "5000123",  # Tribunal Administrativo del Meta
    "5200123",  # Tribunal Administrativo de Nariño
    "5400123",  # Tribunal Administrativo de Norte de Santander
    "8600123",  # Tribunal Administrativo del Putumayo
    "6300123",  # Tribunal Administrativo del Quindío
    "6600123",  # Tribunal Administrativo de Risaralda
    "8800123",  # Tribunal Administrativo de San Andrés
    "6800123",  # Tribunal Administrativo de Santander
    "7000123",  # Tribunal Administrativo de Sucre
    "7300123",  # Tribunal Administrativo del Tolima
    "7600123",  # Tribunal Administrativo del Valle del Cauca
]


class SamaiApiError(Exception):
    """Error al comunicarse con la API de SAMAI."""


class SamaiClient:
    """Cliente para la API REST pública de SAMAI."""

    def __init__(self, base_url: str = BASE_URL, timeout: int = TIMEOUT) -> None:
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()

    def _get(self, path: str) -> Any:
        """GET request a la API. Retorna JSON parsed."""
        url = f"{self.base_url}/{path}"
        try:
            resp = self.session.get(url, timeout=self.timeout)
            resp.raise_for_status()
            if not resp.text.strip():
                return []
            return resp.json()
        except (requests.RequestException, ConnectionError) as e:
            logger.error("SAMAI API error: %s %s", url, e)
            raise SamaiApiError(f"Error consultando {url}: {e}") from e

    def get_actuaciones(self, corporacion: str, radicado: str) -> list[Actuacion]:
        """Obtiene todas las actuaciones de un proceso.

        Retorna lista ordenada por Orden descendente (más reciente primero).
        """
        data = self._get(f"Procesos/HistorialActuaciones/{corporacion}/{radicado}/{MODO}")
        actuaciones = [Actuacion.from_api(item) for item in data]
        actuaciones.sort(key=lambda a: a.orden, reverse=True)
        return actuaciones

    def get_actuaciones_nuevas(
        self, corporacion: str, radicado: str, desde_orden: int
    ) -> list[Actuacion]:
        """Obtiene solo las actuaciones con Orden > desde_orden.

        Útil para detectar novedades: comparar el último Orden conocido
        contra lo que devuelve la API.
        """
        todas = self.get_actuaciones(corporacion, radicado)
        return [a for a in todas if a.orden > desde_orden]

    def get_max_orden(self, corporacion: str, radicado: str) -> int:
        """Retorna el Orden más alto de un proceso, o 0 si no hay actuaciones."""
        actuaciones = self.get_actuaciones(corporacion, radicado)
        if not actuaciones:
            return 0
        return actuaciones[0].orden

    def encontrar_corporacion(self, radicado: str, excluir: list[str] | None = None) -> str | None:
        """Busca la corporacion SAMAI correcta probando Tribunales y Consejo de Estado en paralelo.

        Se usa como fallback cuando la corporacion por defecto (primeros 7 dígitos del radicado)
        no retorna actuaciones. Sólo prueba Tribunales + Consejo de Estado (28 opciones) porque
        los Juzgados normalmente coinciden con los primeros 7 dígitos.

        Retorna el código de corporación si se encuentran actuaciones, None si no.
        """
        excluir_set = set(excluir or [])
        candidatos = [c for c in _TRIBUNALES_Y_CE if c not in excluir_set]

        def _probar(corp: str) -> tuple[str, int]:
            """Retorna (corp, max_orden) donde max_orden es el Orden más alto encontrado (0 si vacío)."""
            try:
                url = f"{self.base_url}/Procesos/HistorialActuaciones/{corp}/{radicado}/{MODO}"
                resp = self.session.get(url, timeout=TIMEOUT_BUSQUEDA)
                resp.raise_for_status()
                if not resp.text.strip():
                    return corp, 0
                data = resp.json()
                if not isinstance(data, list) or not data:
                    return corp, 0
                max_orden = max((item.get("Orden", 0) for item in data), default=0)
                return corp, max_orden
            except Exception:
                return corp, 0

        with ThreadPoolExecutor(max_workers=14) as executor:
            futures = {executor.submit(_probar, c): c for c in candidatos}
            resultados = [f.result() for f in as_completed(futures)]

        validos = [(corp, orden) for corp, orden in resultados if orden > 0]
        if not validos:
            return None

        # Si (en el raro caso) el mismo radicado aparece en varios tribunales,
        # retornar el que tiene la actuación más reciente (mayor Orden).
        mejor_corp, mejor_orden = max(validos, key=lambda x: x[1])
        logger.info(
            "Radicado %s: corporacion encontrada %s (max_orden=%d, total_con_datos=%d)",
            radicado,
            mejor_corp,
            mejor_orden,
            len(validos),
        )
        return mejor_corp

    def buscar_proceso(self, num_proceso: str) -> list[dict]:
        """Busca un proceso en todo SAMAI.

        Retorna lista de dicts con los resultados (puede ser vacía).
        """
        return self._get(f"BuscarProcesoTodoSamai/{num_proceso}/{MODO}")

    def get_datos_proceso(self, corporacion: str, num_proceso: str) -> dict:
        """Obtiene datos completos de un proceso."""
        return self._get(f"ObtenerDatosProcesoGet/{corporacion}/{num_proceso}/{MODO}")

    def get_sujetos_procesales(self, corporacion: str, radicado: str) -> list[dict]:
        """Obtiene las partes procesales (demandante, demandado, etc.)."""
        return self._get(f"Procesos/SujetosProcesales/{corporacion}/{radicado}/{MODO}")

    def get_documento_url(self, corporacion: str, radicado: str, doc_hash: str) -> str:
        """Retorna la URL directa para descargar un documento/providencia."""
        return f"{self.base_url}/DescargarProvidenciaPublica/{corporacion}/{radicado}/{doc_hash}/{MODO}"
