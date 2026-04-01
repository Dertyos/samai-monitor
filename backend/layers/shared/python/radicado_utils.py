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


def parse_ciudad(city_name: str) -> str:
    """Extrae la ciudad de un string tipo 'IBAGUE (TOLIMA)' o 'BOGOTA D.C.'.

    Retorna solo la parte de ciudad, en title case.
    Si no hay paréntesis, retorna el string limpio completo.
    """
    if not city_name:
        return ""
    # "IBAGUE (TOLIMA)" -> "IBAGUE"
    match = re.match(r"^([^(]+)", city_name)
    ciudad = match.group(1).strip() if match else city_name.strip()
    return ciudad.title()


# Mapa de códigos de especialidad judicial colombiana (dígitos 5-6 del radicado)
_ESPECIALIDADES: dict[str, str] = {
    "01": "Civil",
    "02": "Familia",
    "03": "Agrario",
    "04": "Penal",
    "05": "Laboral",
    "06": "Penal Adolescentes",
    "07": "Promiscuo",
    "08": "Ejecucion de Penas",
    "09": "Penal Militar",
    "10": "Civil-Familia",
    "11": "Civil Municipal",
    "12": "Pequenas Causas",
    "20": "Constitucional",
    "23": "Contencioso Administrativo",
    "31": "Penal Municipal",
    "33": "Administrativo",
    "40": "Constitucional",
    "41": "Disciplinario",
    "44": "Jurisdiccion Especial de Paz",
    "50": "Restitucion de Tierras",
}


def extraer_especialidad(radicado: str) -> str:
    """Extrae la especialidad judicial del radicado (dígitos 5-6).

    Retorna el nombre legible (ej: 'Contencioso Administrativo') o
    'Especialidad {código}' si el código no está mapeado.
    """
    norm = normalizar_radicado(radicado)
    codigo = norm[5:7]
    return _ESPECIALIDADES.get(codigo, f"Especialidad {codigo}")


def extraer_corporacion(radicado: str) -> str:
    """Extrae código de corporación (7 dígitos) del radicado.

    Raises:
        RadicadoInvalido: si no es válido.
    """
    norm = normalizar_radicado(radicado)
    return norm[:CORPORACION_LENGTH]
