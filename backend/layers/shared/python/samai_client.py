"""Cliente REST para la API pública de SAMAI.

Responsabilidad única: comunicarse con la API de SAMAI y devolver datos tipados.
No tiene estado, no habla con DynamoDB, no envía correos.
"""
from __future__ import annotations

import logging
from typing import Any

import requests

from models import Actuacion

logger = logging.getLogger(__name__)

BASE_URL = "https://samaicore.consejodeestado.gov.co/api"
TIMEOUT = 30  # seconds
MODO = "2"  # consulta pública


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
