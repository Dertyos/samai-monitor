"""Tests for RamaJudicialClient."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests

from models import Actuacion
from rama_judicial_client import RamaJudicialClient, RamaJudicialApiError

FIXTURES_DIR = Path(__file__).parent / "fixtures"
RADICADO = "11001400300120240012600"
ID_PROCESO = 149525880


@pytest.fixture
def cpnu_actuaciones_response() -> dict:
    with open(FIXTURES_DIR / "cpnu_actuaciones.json") as f:
        return json.load(f)


@pytest.fixture
def cpnu_proceso_response() -> dict:
    with open(FIXTURES_DIR / "cpnu_proceso.json") as f:
        return json.load(f)


@pytest.fixture
def client() -> RamaJudicialClient:
    return RamaJudicialClient()


def _mock_get(client: RamaJudicialClient, response_data: dict):
    """Helper: patch session.get to return response_data as JSON."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = json.dumps(response_data)
    mock_resp.json.return_value = response_data
    return patch.object(client.session, "get", return_value=mock_resp)


class TestBuscarPorRadicado:
    def test_retorna_lista_de_procesos(self, client, cpnu_proceso_response):
        with _mock_get(client, cpnu_proceso_response):
            procesos = client.buscar_por_radicado(RADICADO)

        assert len(procesos) == 1
        assert procesos[0]["idProceso"] == ID_PROCESO
        assert procesos[0]["despacho"] == "JUZGADO 001 CIVIL MUNICIPAL DE BOGOTÁ"

    def test_radicado_no_encontrado_retorna_lista_vacia(self, client):
        empty = {
            "tipoConsulta": "NumeroRadicacion",
            "procesos": [],
            "paginacion": {"cantidadRegistros": 0, "registrosPagina": 20, "cantidadPaginas": 0, "pagina": 1},
        }
        with _mock_get(client, empty):
            result = client.buscar_por_radicado(RADICADO)

        assert result == []

    def test_error_http_lanza_excepcion(self, client):
        with patch.object(client.session, "get", side_effect=requests.ConnectionError("timeout")):
            with pytest.raises(RamaJudicialApiError):
                client.buscar_por_radicado(RADICADO)

    def test_http_400_lanza_excepcion(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 400
        mock_resp.json.return_value = {"Message": "Radicado no válido"}
        with patch.object(client.session, "get", return_value=mock_resp):
            with pytest.raises(RamaJudicialApiError, match="Radicado no válido"):
                client.buscar_por_radicado(RADICADO)


class TestGetActuaciones:
    def test_convierte_a_objetos_actuacion(self, client, cpnu_actuaciones_response):
        with _mock_get(client, cpnu_actuaciones_response):
            acts = client.get_actuaciones(ID_PROCESO, pagina=1)

        assert len(acts) == 5
        assert all(isinstance(a, Actuacion) for a in acts)
        # Ordenadas desc por consActuacion (primera = más reciente)
        assert acts[0].orden == 5
        assert acts[-1].orden == 1

    def test_mapeo_de_campos(self, client, cpnu_actuaciones_response):
        with _mock_get(client, cpnu_actuaciones_response):
            acts = client.get_actuaciones(ID_PROCESO, pagina=1)

        primera = acts[0]
        assert primera.radicado == RADICADO
        assert primera.nombre == "Envío Expediente"
        assert primera.anotacion == "SE ENVIA A LA CORTE CONSTITUCIONAL"
        assert primera.codigo == "00"

    def test_pagina_vacia_retorna_lista_vacia(self, client):
        empty = {"actuaciones": [], "paginacion": {"cantidadRegistros": 0}}
        with _mock_get(client, empty):
            acts = client.get_actuaciones(ID_PROCESO, pagina=99)

        assert acts == []


class TestGetTodasActuaciones:
    def test_retorna_todas_en_una_pagina(self, client, cpnu_actuaciones_response):
        """Con < 40 actuaciones en la respuesta, termina en la primera página."""
        with _mock_get(client, cpnu_actuaciones_response):
            todas = client.get_todas_actuaciones(ID_PROCESO)

        assert len(todas) == 5

    def test_pagina_sin_resultados_termina_loop(self, client):
        empty = {"actuaciones": [], "paginacion": {"cantidadRegistros": 0}}
        with _mock_get(client, empty):
            todas = client.get_todas_actuaciones(ID_PROCESO)

        assert todas == []


class TestGetActuacionesNuevas:
    def test_filtra_mayor_que_desde_cons(self, client, cpnu_actuaciones_response):
        with _mock_get(client, cpnu_actuaciones_response):
            nuevas = client.get_actuaciones_nuevas(ID_PROCESO, desde_cons=3)

        assert len(nuevas) == 2
        assert all(a.orden > 3 for a in nuevas)
        assert {a.orden for a in nuevas} == {4, 5}

    def test_desde_cons_0_retorna_todas(self, client, cpnu_actuaciones_response):
        with _mock_get(client, cpnu_actuaciones_response):
            nuevas = client.get_actuaciones_nuevas(ID_PROCESO, desde_cons=0)

        assert len(nuevas) == 5

    def test_ya_actualizado_retorna_lista_vacia(self, client, cpnu_actuaciones_response):
        with _mock_get(client, cpnu_actuaciones_response):
            nuevas = client.get_actuaciones_nuevas(ID_PROCESO, desde_cons=5)

        assert nuevas == []

    def test_sin_actuaciones_retorna_lista_vacia(self, client):
        empty = {"actuaciones": [], "paginacion": {"cantidadRegistros": 0}}
        with _mock_get(client, empty):
            nuevas = client.get_actuaciones_nuevas(ID_PROCESO, desde_cons=0)

        assert nuevas == []


class TestGetMaxConsActuacion:
    def test_retorna_el_mas_alto(self, client, cpnu_actuaciones_response):
        with _mock_get(client, cpnu_actuaciones_response):
            max_cons = client.get_max_cons_actuacion(ID_PROCESO)

        assert max_cons == 5  # primera actuación en respuesta desc

    def test_sin_actuaciones_retorna_0(self, client):
        empty = {"actuaciones": [], "paginacion": {"cantidadRegistros": 0}}
        with _mock_get(client, empty):
            assert client.get_max_cons_actuacion(ID_PROCESO) == 0
