"""Cliente para SIUGJ (Sistema Integrado de Uso de la Gestión Judicial).

API descubierta por ingeniería inversa del JS del portal SIUGJ.
URL base: https://siugj.ramajudicial.gov.co/
Endpoint: modulosEspeciales_SIUGJ/paginasFunciones/funcionesBuscadorProceso.php

Técnica:
  POST application/x-www-form-urlencoded
  Parámetros JSON codificados en base64 (función bE() del JS original)
  reCAPTCHA v2 visible en el frontend pero el servidor PHP NO lo valida

Cubre procesos de la Rama Judicial ordinaria bajo el sistema
Justicia XXI cliente-servidor (legado) — los que aún no migraron a CPNU.

Identificador: codigoUnicoProceso = radicado de 23 dígitos (mismo formato que CPNU).
Clave de diff: idRegistro (int incremental) equivale al Orden de SAMAI.
"""
from __future__ import annotations

import base64
import json
import logging
from typing import Any

import requests

from models import Actuacion

logger = logging.getLogger(__name__)

BASE_URL = "https://siugj.ramajudicial.gov.co"
ENDPOINT = (
    f"{BASE_URL}/modulosEspeciales_SIUGJ/paginasFunciones/funcionesBuscadorProceso.php"
)
TIMEOUT = 20

_HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded",
    "Origin": BASE_URL,
    "Referer": f"{BASE_URL}/principalPortal/consultarProceso.php",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json, text/plain, */*",
}


class SiugjApiError(Exception):
    """Error al comunicarse con SIUGJ."""


class SiugjClient:
    """Cliente para la API PHP de SIUGJ.

    Busca procesos del sistema Justicia XXI cliente-servidor (procesos que
    no han migrado al sistema web de CPNU).
    """

    def __init__(self, endpoint: str = ENDPOINT, timeout: int = TIMEOUT) -> None:
        self.endpoint = endpoint
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(_HEADERS)

    def _b64(self, obj: Any) -> str:
        """Codifica objeto en base64 — función bE() del JS original.

        Si obj es str → codifica directamente.
        Si obj es dict → serializa a JSON compacto antes de codificar.
        """
        if isinstance(obj, str):
            raw = obj.encode()
        else:
            raw = json.dumps(obj, separators=(",", ":")).encode()
        return base64.b64encode(raw).decode()

    def _post(self, funcion: str, params: dict[str, str]) -> Any:
        """POST al endpoint PHP. Retorna JSON parsed."""
        body_parts = [f"funcion={funcion}"]
        body_parts.extend(f"{k}={v}" for k, v in params.items())
        body = "&".join(body_parts)
        try:
            resp = self.session.post(self.endpoint, data=body, timeout=self.timeout)
            resp.raise_for_status()
            if not resp.text.strip():
                return {}
            return resp.json()
        except (requests.RequestException, ConnectionError) as e:
            logger.error("SIUGJ API error: %s", e)
            raise SiugjApiError(f"Error consultando SIUGJ: {e}") from e

    def buscar_por_radicado(self, radicado: str, pagina: int = 1) -> list[dict]:
        """Busca procesos por número de radicado de 23 dígitos.

        funcion=2 con parámetro 'remino' (typo en JS original, no 'termino').
        Retorna lista de dicts con codigoUnicoProceso, despacho, etc.
        """
        result = self._post(
            "2",
            {"cadObj": self._b64({"remino": radicado, "pagina": pagina})},
        )
        return result.get("registros", [])

    def get_actuaciones(self, codigo_unico_proceso: str) -> list[Actuacion]:
        """Obtiene todas las actuaciones de un proceso.

        funcion=3 con cA = base64(codigoUnicoProceso).
        Clave de diff: idRegistro (int incremental).
        """
        result = self._post("3", {"cA": self._b64(codigo_unico_proceso)})
        registros = result.get("registros", [])
        return [
            Actuacion.from_siugj_api(r, radicado=codigo_unico_proceso)
            for r in registros
        ]

    def get_actuaciones_nuevas(
        self, codigo_unico_proceso: str, desde_id: int
    ) -> list[Actuacion]:
        """Retorna actuaciones con idRegistro > desde_id."""
        actuaciones = self.get_actuaciones(codigo_unico_proceso)
        return [a for a in actuaciones if a.orden > desde_id]

    def get_max_id(self, codigo_unico_proceso: str) -> int:
        """Retorna el idRegistro más alto (0 si no hay actuaciones)."""
        actuaciones = self.get_actuaciones(codigo_unico_proceso)
        if not actuaciones:
            return 0
        return max(a.orden for a in actuaciones)
