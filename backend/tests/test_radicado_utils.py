"""Tests for radicado_utils — TDD: escribimos tests primero."""
from __future__ import annotations

import pytest
from radicado_utils import (
    normalizar_radicado,
    formatear_radicado,
    validar_radicado,
    extraer_corporacion,
    RadicadoInvalido,
)


class TestNormalizarRadicado:
    """normalizar_radicado: quita guiones y espacios, retorna solo dígitos."""

    def test_con_guiones(self):
        assert normalizar_radicado("73001-23-33-000-2019-00343-00") == "73001233300020190034300"

    def test_sin_guiones(self):
        assert normalizar_radicado("73001233300020190034300") == "73001233300020190034300"

    def test_con_espacios(self):
        assert normalizar_radicado(" 73001-23-33-000-2019-00343-00 ") == "73001233300020190034300"

    def test_vacio_raises(self):
        with pytest.raises(RadicadoInvalido):
            normalizar_radicado("")

    def test_letras_raises(self):
        with pytest.raises(RadicadoInvalido):
            normalizar_radicado("abc-def-ghi")

    def test_muy_corto_raises(self):
        with pytest.raises(RadicadoInvalido):
            normalizar_radicado("12345")


class TestFormatearRadicado:
    """formatear_radicado: de '73001233300020190034300' a '73001-23-33-000-2019-00343-00'."""

    def test_formato_estandar(self):
        assert formatear_radicado("73001233300020190034300") == "73001-23-33-000-2019-00343-00"

    def test_otro_radicado(self):
        assert formatear_radicado("73001233300020230047100") == "73001-23-33-000-2023-00471-00"

    def test_radicado_con_instancia(self):
        # Radicado con instancia 01
        assert formatear_radicado("73001333300620250017601") == "73001-33-33-006-2025-00176-01"

    def test_ya_formateado_pasa_por_normalizar(self):
        """Si le pasan uno con guiones, normaliza primero y formatea."""
        assert formatear_radicado("73001-23-33-000-2019-00343-00") == "73001-23-33-000-2019-00343-00"

    def test_invalido_raises(self):
        with pytest.raises(RadicadoInvalido):
            formatear_radicado("12345")


class TestValidarRadicado:
    """validar_radicado: retorna True/False sin lanzar excepción."""

    def test_valido_con_guiones(self):
        assert validar_radicado("73001-23-33-000-2019-00343-00") is True

    def test_valido_sin_guiones(self):
        assert validar_radicado("73001233300020190034300") is True

    def test_invalido(self):
        assert validar_radicado("12345") is False

    def test_vacio(self):
        assert validar_radicado("") is False

    def test_con_letras(self):
        assert validar_radicado("abc123") is False

    def test_23_digitos(self):
        """Un radicado normalizado tiene exactamente 23 dígitos."""
        assert validar_radicado("73001233300020190034300") is True  # 23 dígitos
        assert validar_radicado("7300123330002019003430") is False  # 22 dígitos
        assert validar_radicado("730012333000201900343001") is False  # 24 dígitos


class TestExtraerCorporacion:
    """extraer_corporacion: extrae código de corporación (7 dígitos) del radicado."""

    def test_de_radicado_normalizado(self):
        assert extraer_corporacion("73001233300020190034300") == "7300123"

    def test_de_radicado_con_guiones(self):
        assert extraer_corporacion("73001-23-33-000-2019-00343-00") == "7300123"

    def test_tribunal_cundinamarca(self):
        assert extraer_corporacion("25000-23-33-000-2020-00100-00") == "2500023"

    def test_consejo_estado(self):
        assert extraer_corporacion("11001-03-33-000-2020-00100-00") == "1100103"

    def test_invalido_raises(self):
        with pytest.raises(RadicadoInvalido):
            extraer_corporacion("12345")
