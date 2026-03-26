"""Cliente REST para la API pública del CPNU (Rama Judicial de Colombia).

API descubierta por ingeniería inversa del bundle JS de la SPA Vue.js.
Base URL: https://consultaprocesos.ramajudicial.gov.co:448/api/v2
Documentación completa: DOCS/RAMA_JUDICIAL_API.md

Responsabilidad única: comunicarse con la API del CPNU y devolver datos tipados.
No tiene estado, no habla con DynamoDB, no envía correos.
"""
from __future__ import annotations

import logging
from typing import Any

import requests

from models import Actuacion

logger = logging.getLogger(__name__)

BASE_URL = "https://consultaprocesos.ramajudicial.gov.co:448/api/v2"
TIMEOUT = 20  # seconds

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Origin": "https://consultaprocesos.ramajudicial.gov.co",
    "Referer": "https://consultaprocesos.ramajudicial.gov.co/",
    "Accept": "application/json, text/plain, */*",
}


class RamaJudicialApiError(Exception):
    """Error al comunicarse con la API del CPNU."""


class RamaJudicialClient:
    """Cliente para la API REST pública del CPNU.

    Consultas públicas no requieren autenticación (CORS abierto).
    El campo consecutivo es 'consActuacion' (equivalente al 'Orden' de SAMAI).
    """

    def __init__(self, base_url: str = BASE_URL, timeout: int = TIMEOUT) -> None:
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(_HEADERS)

    def _get(self, path: str, params: dict | None = None) -> Any:
        """GET request a la API. Retorna JSON parsed."""
        url = f"{self.base_url}/{path}"
        try:
            resp = self.session.get(url, params=params, timeout=self.timeout)
            if resp.status_code == 400:
                raise RamaJudicialApiError(
                    resp.json().get("Message", f"HTTP 400 en {url}")
                )
            resp.raise_for_status()
            if not resp.text.strip():
                return {}
            return resp.json()
        except RamaJudicialApiError:
            raise
        except (requests.RequestException, ConnectionError) as e:
            logger.error("CPNU API error: %s %s", url, e)
            raise RamaJudicialApiError(f"Error consultando {url}: {e}") from e

    def buscar_por_radicado(self, radicado: str) -> list[dict]:
        """Busca procesos por número de radicación (23 dígitos sin guiones).

        Un radicado puede retornar múltiples procesos si el caso ha pasado
        por distintos despachos (primera instancia, apelación, etc.).
        Cada resultado incluye idProceso, despacho, sujetosProcesales.
        """
        data = self._get(
            "Procesos/Consulta/NumeroRadicacion",
            params={"numero": radicado, "SoloActivos": "false", "pagina": 1},
        )
        return data.get("procesos", [])

    def get_detalle(self, id_proceso: int) -> dict:
        """Obtiene datos detallados de un proceso (despacho, ponente, tipo, etc.)."""
        return self._get(f"Proceso/Detalle/{id_proceso}")

    def get_sujetos(self, id_proceso: int) -> list[dict]:
        """Obtiene las partes procesales (demandante, demandado, etc.)."""
        data = self._get(f"Proceso/Sujetos/{id_proceso}", params={"pagina": 1})
        return data.get("sujetos", [])

    def get_actuaciones(self, id_proceso: int, pagina: int = 1) -> list[Actuacion]:
        """Obtiene actuaciones de una página (40 por página, descendente por consActuacion)."""
        data = self._get(
            f"Proceso/Actuaciones/{id_proceso}", params={"pagina": pagina}
        )
        return [Actuacion.from_rama_judicial_api(a) for a in data.get("actuaciones", [])]

    def get_todas_actuaciones(self, id_proceso: int) -> list[Actuacion]:
        """Obtiene TODAS las actuaciones paginando automáticamente (40 por página)."""
        todas: list[Actuacion] = []
        pagina = 1
        while True:
            acts = self.get_actuaciones(id_proceso, pagina=pagina)
            if not acts:
                break
            todas.extend(acts)
            # 'cant' en cada actuación = total del proceso
            total = int(acts[0].registro or "0") if False else 0
            # Paramos si ya tenemos todos (cant es el mismo en todos los ítems)
            pagina += 1
            if len(acts) < 40:  # última página (40 es el tamaño de página)
                break
        return todas

    def get_actuaciones_nuevas(
        self, id_proceso: int, desde_cons: int
    ) -> list[Actuacion]:
        """Retorna solo actuaciones con consActuacion > desde_cons.

        Recorre páginas mientras encuentre actuaciones nuevas (vienen en orden desc).
        """
        nuevas: list[Actuacion] = []
        pagina = 1
        while True:
            acts = self.get_actuaciones(id_proceso, pagina=pagina)
            if not acts:
                break
            for a in acts:
                if a.orden > desde_cons:
                    nuevas.append(a)
                else:
                    # Orden descendente — todo lo que sigue es ≤ desde_cons
                    return nuevas
            if len(acts) < 40:  # última página
                break
            pagina += 1
        return nuevas

    def get_max_cons_actuacion(self, id_proceso: int) -> int:
        """Retorna el consActuacion más alto (0 si no hay actuaciones)."""
        acts = self.get_actuaciones(id_proceso, pagina=1)
        if not acts:
            return 0
        return acts[0].orden  # primer item = el más reciente (desc)
