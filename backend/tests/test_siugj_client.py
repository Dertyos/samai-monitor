"""Tests para SiugjClient — cliente del sistema SIUGJ (Justicia XXI legado).

Patrón idéntico a test_rama_judicial_client.py.
Fixtures: siugj_buscar.json, siugj_actuaciones.json
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


def _mock_response(data: dict, status: int = 200) -> MagicMock:
    mock = MagicMock()
    mock.status_code = status
    mock.text = json.dumps(data)
    mock.json.return_value = data
    mock.raise_for_status = MagicMock()
    return mock


# ---------------------------------------------------------------------------
# Importar bajo sys.path del layer
# ---------------------------------------------------------------------------
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "layers" / "shared" / "python"))

from siugj_client import SiugjClient, SiugjApiError  # noqa: E402


# ---------------------------------------------------------------------------
# Tests buscar_por_radicado
# ---------------------------------------------------------------------------
class TestBuscarPorRadicado:
    def test_retorna_lista_de_registros(self):
        fixture = _load("siugj_buscar.json")
        client = SiugjClient()
        with patch.object(client.session, "post", return_value=_mock_response(fixture)):
            result = client.buscar_por_radicado("66170310500120160001100")
        assert len(result) == 1
        assert result[0]["codigoUnicoProceso"] == "66170310500120160001100"
        assert result[0]["despacho"] == "JUZGADO 001 LABORAL DEL CIRCUITO DE DOSQUEBRADAS"

    def test_sin_resultados_retorna_lista_vacia(self):
        client = SiugjClient()
        with patch.object(
            client.session, "post", return_value=_mock_response({"numReg": 0, "registros": []})
        ):
            result = client.buscar_por_radicado("00000000000000000000000")
        assert result == []

    def test_respuesta_vacia_retorna_lista_vacia(self):
        mock = MagicMock()
        mock.status_code = 200
        mock.text = ""
        mock.raise_for_status = MagicMock()
        client = SiugjClient()
        with patch.object(client.session, "post", return_value=mock):
            result = client.buscar_por_radicado("66170310500120160001100")
        assert result == []

    def test_error_http_lanza_excepcion(self):
        client = SiugjClient()
        with patch.object(
            client.session, "post", side_effect=requests.RequestException("timeout")
        ):
            with pytest.raises(SiugjApiError):
                client.buscar_por_radicado("66170310500120160001100")

    def test_envia_funcion_2_en_body(self):
        fixture = _load("siugj_buscar.json")
        client = SiugjClient()
        with patch.object(client.session, "post", return_value=_mock_response(fixture)) as mock_post:
            client.buscar_por_radicado("66170310500120160001100")
        body = mock_post.call_args[1]["data"]
        assert "funcion=2" in body
        assert "cadObj=" in body


# ---------------------------------------------------------------------------
# Tests get_actuaciones
# ---------------------------------------------------------------------------
class TestGetActuaciones:
    def test_retorna_lista_de_actuaciones(self):
        fixture = _load("siugj_actuaciones.json")
        client = SiugjClient()
        with patch.object(client.session, "post", return_value=_mock_response(fixture)):
            acts = client.get_actuaciones("66170310500120160001100")
        assert len(acts) == 5

    def test_mapea_campos_correctamente(self):
        fixture = _load("siugj_actuaciones.json")
        client = SiugjClient()
        with patch.object(client.session, "post", return_value=_mock_response(fixture)):
            acts = client.get_actuaciones("66170310500120160001100")
        # idRegistro → orden
        ordenes = [a.orden for a in acts]
        assert 5 in ordenes
        assert 1 in ordenes
        # nombre
        act5 = next(a for a in acts if a.orden == 5)
        assert act5.nombre == "Audiencia Programada"
        # anotacion
        assert "audiencia" in act5.anotacion.lower()

    def test_radicado_se_propaga(self):
        fixture = _load("siugj_actuaciones.json")
        client = SiugjClient()
        with patch.object(client.session, "post", return_value=_mock_response(fixture)):
            acts = client.get_actuaciones("66170310500120160001100")
        for a in acts:
            assert a.radicado == "66170310500120160001100"

    def test_envia_funcion_3_en_body(self):
        fixture = _load("siugj_actuaciones.json")
        client = SiugjClient()
        with patch.object(client.session, "post", return_value=_mock_response(fixture)) as mock_post:
            client.get_actuaciones("66170310500120160001100")
        body = mock_post.call_args[1]["data"]
        assert "funcion=3" in body
        assert "cA=" in body


# ---------------------------------------------------------------------------
# Tests get_actuaciones_nuevas
# ---------------------------------------------------------------------------
class TestGetActuacionesNuevas:
    def test_filtra_correctamente(self):
        fixture = _load("siugj_actuaciones.json")
        client = SiugjClient()
        with patch.object(client.session, "post", return_value=_mock_response(fixture)):
            nuevas = client.get_actuaciones_nuevas("66170310500120160001100", desde_id=3)
        assert len(nuevas) == 2
        assert all(a.orden > 3 for a in nuevas)

    def test_sin_nuevas_retorna_vacio(self):
        fixture = _load("siugj_actuaciones.json")
        client = SiugjClient()
        with patch.object(client.session, "post", return_value=_mock_response(fixture)):
            nuevas = client.get_actuaciones_nuevas("66170310500120160001100", desde_id=999)
        assert nuevas == []

    def test_todas_nuevas_si_desde_id_es_cero(self):
        fixture = _load("siugj_actuaciones.json")
        client = SiugjClient()
        with patch.object(client.session, "post", return_value=_mock_response(fixture)):
            nuevas = client.get_actuaciones_nuevas("66170310500120160001100", desde_id=0)
        assert len(nuevas) == 5


# ---------------------------------------------------------------------------
# Tests get_max_id
# ---------------------------------------------------------------------------
class TestGetMaxId:
    def test_retorna_el_mayor_id_registro(self):
        fixture = _load("siugj_actuaciones.json")
        client = SiugjClient()
        with patch.object(client.session, "post", return_value=_mock_response(fixture)):
            max_id = client.get_max_id("66170310500120160001100")
        assert max_id == 5

    def test_retorna_cero_si_no_hay_actuaciones(self):
        client = SiugjClient()
        with patch.object(
            client.session, "post", return_value=_mock_response({"numReg": 0, "registros": []})
        ):
            max_id = client.get_max_id("66170310500120160001100")
        assert max_id == 0


# ---------------------------------------------------------------------------
# Tests _b64 (codificación base64)
# ---------------------------------------------------------------------------
class TestB64:
    def test_dict_se_codifica_correctamente(self):
        import base64
        client = SiugjClient()
        encoded = client._b64({"remino": "test", "pagina": 1})
        decoded = json.loads(base64.b64decode(encoded).decode())
        assert decoded == {"remino": "test", "pagina": 1}

    def test_string_se_codifica_correctamente(self):
        import base64
        client = SiugjClient()
        encoded = client._b64("66170310500120160001100")
        decoded = base64.b64decode(encoded).decode()
        assert decoded == "66170310500120160001100"
