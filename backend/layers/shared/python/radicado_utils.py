"""Utilidades para validación y formato de radicados judiciales colombianos.

Formato radicado: XXXXX-YY-ZZ-WWW-AAAA-BBBBB-CC (23 dígitos sin guiones)
- XXXXX: código municipio (5)
- YY: código especialidad (2)
- ZZ: código despacho tipo (2)
- WWW: código despacho número (3)
- AAAA: año radicación (4)
- BBBBB: consecutivo (5)
- CC: instancia (2)

Código corporación = primeros 7 dígitos (municipio + especialidad).
"""
from __future__ import annotations

import re

RADICADO_LENGTH = 23
CORPORACION_LENGTH = 7


class RadicadoInvalido(ValueError):
    """Radicado no tiene formato válido."""


def normalizar_radicado(radicado: str) -> str:
    """Quita guiones y espacios, retorna solo dígitos.

    Raises:
        RadicadoInvalido: si el resultado no tiene exactamente 23 dígitos.
    """
    limpio = re.sub(r"[\s\-]", "", radicado.strip())
    if not limpio:
        raise RadicadoInvalido("Radicado vacío")
    if not limpio.isdigit():
        raise RadicadoInvalido(f"Radicado contiene caracteres no numéricos: {radicado!r}")
    if len(limpio) != RADICADO_LENGTH:
        raise RadicadoInvalido(
            f"Radicado debe tener {RADICADO_LENGTH} dígitos, tiene {len(limpio)}: {radicado!r}"
        )
    return limpio


def formatear_radicado(radicado: str) -> str:
    """Formatea radicado a XXXXX-YY-ZZ-WWW-AAAA-BBBBB-CC.

    Acepta tanto con guiones como sin guiones.

    Raises:
        RadicadoInvalido: si no es válido.
    """
    norm = normalizar_radicado(radicado)
    return f"{norm[0:5]}-{norm[5:7]}-{norm[7:9]}-{norm[9:12]}-{norm[12:16]}-{norm[16:21]}-{norm[21:23]}"


def validar_radicado(radicado: str) -> bool:
    """Retorna True si el radicado es válido, False en caso contrario."""
    try:
        normalizar_radicado(radicado)
        return True
    except (RadicadoInvalido, Exception):
        return False


def extraer_corporacion(radicado: str) -> str:
    """Extrae código de corporación (7 dígitos) del radicado.

    Raises:
        RadicadoInvalido: si no es válido.
    """
    norm = normalizar_radicado(radicado)
    return norm[:CORPORACION_LENGTH]
