"""Tests for samai_client — TDD: tests primero, requests-mock para no tocar la red."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import requests_mock as rm

from samai_client import SamaiClient, SamaiApiError
from models import Actuacion

FIXTURES = Path(__file__).parent / "fixtures"
BASE_URL = "https://samaicore.consejodeestado.gov.co/api"

CORP = "7300123"
RADICADO = "73001233300020190034300"


@pytest.fixture
def client() -> SamaiClient:
    return SamaiClient()


@pytest.fixture
def actuaciones_json() -> list[dict]:
    with open(FIXTURES / "samai_actuaciones.json") as f:
        return json.load(f)


@pytest.fixture
def proceso_json() -> dict:
    with open(FIXTURES / "samai_proceso.json") as f:
        return json.load(f)


class TestGetActuaciones:
    """SamaiClient.get_actuaciones: obtiene historial de actuaciones de un proceso."""

    def test_retorna_lista_de_actuaciones(self, client: SamaiClient, actuaciones_json: list[dict]):
        with rm.Mocker() as m:
            url = f"{BASE_URL}/Procesos/HistorialActuaciones/{CORP}/{RADICADO}/2"
            m.get(url, json=actuaciones_json)

            result = client.get_actuaciones(CORP, RADICADO)

            assert isinstance(result, list)
            assert len(result) == len(actuaciones_json)
            assert all(isinstance(a, Actuacion) for a in result)

    def test_actuaciones_ordenadas_por_orden_descendente(
        self, client: SamaiClient, actuaciones_json: list[dict]
    ):
        with rm.Mocker() as m:
            url = f"{BASE_URL}/Procesos/HistorialActuaciones/{CORP}/{RADICADO}/2"
            m.get(url, json=actuaciones_json)

            result = client.get_actuaciones(CORP, RADICADO)

            ordenes = [a.orden for a in result]
            assert ordenes == sorted(ordenes, reverse=True)

    def test_primera_actuacion_tiene_campos_correctos(
        self, client: SamaiClient, actuaciones_json: list[dict]
    ):
        with rm.Mocker() as m:
            url = f"{BASE_URL}/Procesos/HistorialActuaciones/{CORP}/{RADICADO}/2"
            m.get(url, json=actuaciones_json)

            result = client.get_actuaciones(CORP, RADICADO)
            primera = result[0]

            assert primera.radicado == RADICADO
            assert primera.orden == 177
            assert primera.nombre == "Fijacion estado"

    def test_api_error_raises(self, client: SamaiClient):
        with rm.Mocker() as m:
            url = f"{BASE_URL}/Procesos/HistorialActuaciones/{CORP}/{RADICADO}/2"
            m.get(url, status_code=500)

            with pytest.raises(SamaiApiError):
                client.get_actuaciones(CORP, RADICADO)

    def test_timeout_raises(self, client: SamaiClient):
        with rm.Mocker() as m:
            url = f"{BASE_URL}/Procesos/HistorialActuaciones/{CORP}/{RADICADO}/2"
            m.get(url, exc=ConnectionError("timeout"))

            with pytest.raises(SamaiApiError):
                client.get_actuaciones(CORP, RADICADO)

    def test_respuesta_vacia(self, client: SamaiClient):
        with rm.Mocker() as m:
            url = f"{BASE_URL}/Procesos/HistorialActuaciones/{CORP}/{RADICADO}/2"
            m.get(url, json=[])

            result = client.get_actuaciones(CORP, RADICADO)
            assert result == []


class TestGetActuacionesNuevas:
    """SamaiClient.get_actuaciones_nuevas: filtra solo las posteriores a un Orden dado."""

    def test_filtra_por_orden(self, client: SamaiClient, actuaciones_json: list[dict]):
        with rm.Mocker() as m:
            url = f"{BASE_URL}/Procesos/HistorialActuaciones/{CORP}/{RADICADO}/2"
            m.get(url, json=actuaciones_json)

            # Solo las que tengan Orden > 175
            result = client.get_actuaciones_nuevas(CORP, RADICADO, desde_orden=175)

            assert len(result) == 2  # Orden 177 y 176
            assert all(a.orden > 175 for a in result)

    def test_desde_cero_retorna_todas(self, client: SamaiClient, actuaciones_json: list[dict]):
        with rm.Mocker() as m:
            url = f"{BASE_URL}/Procesos/HistorialActuaciones/{CORP}/{RADICADO}/2"
            m.get(url, json=actuaciones_json)

            result = client.get_actuaciones_nuevas(CORP, RADICADO, desde_orden=0)
            assert len(result) == len(actuaciones_json)

    def test_orden_mayor_al_maximo_retorna_vacio(
        self, client: SamaiClient, actuaciones_json: list[dict]
    ):
        with rm.Mocker() as m:
            url = f"{BASE_URL}/Procesos/HistorialActuaciones/{CORP}/{RADICADO}/2"
            m.get(url, json=actuaciones_json)

            result = client.get_actuaciones_nuevas(CORP, RADICADO, desde_orden=999)
            assert result == []


class TestBuscarProceso:
    """SamaiClient.buscar_proceso: busca un proceso en todo SAMAI."""

    def test_proceso_encontrado(self, client: SamaiClient):
        mock_response = [{"NumProceso": RADICADO, "Corporacion": CORP}]
        with rm.Mocker() as m:
            url = f"{BASE_URL}/BuscarProcesoTodoSamai/{RADICADO}/2"
            m.get(url, json=mock_response)

            result = client.buscar_proceso(RADICADO)
            assert isinstance(result, list)
            assert len(result) == 1

    def test_proceso_no_encontrado(self, client: SamaiClient):
        with rm.Mocker() as m:
            url = f"{BASE_URL}/BuscarProcesoTodoSamai/99999999999999999999999/2"
            m.get(url, json=[])

            result = client.buscar_proceso("99999999999999999999999")
            assert result == []

    def test_api_error(self, client: SamaiClient):
        with rm.Mocker() as m:
            url = f"{BASE_URL}/BuscarProcesoTodoSamai/{RADICADO}/2"
            m.get(url, status_code=503)

            with pytest.raises(SamaiApiError):
                client.buscar_proceso(RADICADO)


class TestGetMaxOrden:
    """SamaiClient.get_max_orden: retorna el Orden más alto de un proceso."""

    def test_retorna_maximo(self, client: SamaiClient, actuaciones_json: list[dict]):
        with rm.Mocker() as m:
            url = f"{BASE_URL}/Procesos/HistorialActuaciones/{CORP}/{RADICADO}/2"
            m.get(url, json=actuaciones_json)

            result = client.get_max_orden(CORP, RADICADO)
            assert result == 177

    def test_proceso_sin_actuaciones(self, client: SamaiClient):
        with rm.Mocker() as m:
            url = f"{BASE_URL}/Procesos/HistorialActuaciones/{CORP}/{RADICADO}/2"
            m.get(url, json=[])

            result = client.get_max_orden(CORP, RADICADO)
            assert result == 0
