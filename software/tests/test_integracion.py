"""Pruebas sin Ollama para el puente y el trabajador de IA."""

import csv
import json
from unittest.mock import Mock

from puente_detector_ia import encolar_evento, publicar_evento
from trabajador_ia import procesar_cola


EVENTO = {
    "evento": "reduccion_corriente_dc", "inversor": 2,
    "reduccion_porcentual": 40, "duracion_minutos": 15,
    "generacion_esperada": True,
}


def test_alerta_se_guarda_antes_de_ia(tmp_path):
    info = publicar_evento(EVENTO, tmp_path)
    assert info["alerta_guardada"] is True
    assert info["ia_encolada"] is True
    with (tmp_path / "alertas_anomalias.csv").open(encoding="utf-8") as f:
        filas = list(csv.DictReader(f))
    assert len(filas) == 1
    assert filas[0]["categoria"] == "reduccion_corriente_dc"
    assert json.loads(filas[0]["evento_json"]) == EVENTO
    assert len(list((tmp_path / "cola_ia").glob("*.json"))) == 1


def test_no_modifica_csv_original_de_muestra(tmp_path):
    original = tmp_path / "datos_seslab.csv"
    original.write_text("fecha,potencia\n2026-01-01,200\n", encoding="utf-8")
    antes = original.read_bytes()
    publicar_evento(EVENTO, tmp_path / "salidas")
    assert original.read_bytes() == antes


def test_ia_completa_guarda_resultado_y_libera_cola(tmp_path):
    info = publicar_evento(EVENTO, tmp_path)
    simulado = Mock(return_value={"estado_ia": "completo", "interpretacion": {}})
    assert procesar_cola(tmp_path, simulado) == ["completo"]
    simulado.assert_called_once_with(EVENTO)
    assert not list((tmp_path / "cola_ia").glob("*.json"))
    ruta = tmp_path / "resultados_ia" / (info["id_evento"] + ".json")
    assert json.loads(ruta.read_text(encoding="utf-8"))["resultado"]["estado_ia"] == "completo"


def test_fallo_de_ia_deja_alerta_y_pendiente(tmp_path):
    info = publicar_evento(EVENTO, tmp_path)
    falla = Mock(return_value={"estado_ia": "no_disponible"})
    assert procesar_cola(tmp_path, falla) == ["no_disponible"]
    assert (tmp_path / "alertas_anomalias.csv").exists()
    assert (tmp_path / "cola_ia" / (info["id_evento"] + ".json")).exists()
    assert (tmp_path / "resultados_ia" / (info["id_evento"] + ".json")).exists()


def test_pendiente_se_reintenta_cuando_ia_vuelve(tmp_path):
    info = publicar_evento(EVENTO, tmp_path)
    procesar_cola(tmp_path, Mock(return_value={"estado_ia": "no_disponible"}))
    assert procesar_cola(tmp_path, Mock(return_value={"estado_ia": "completo"})) == ["completo"]
    assert not (tmp_path / "cola_ia" / (info["id_evento"] + ".json")).exists()
    with (tmp_path / "alertas_anomalias.csv").open(encoding="utf-8") as f:
        assert len(list(csv.DictReader(f))) == 1  # Sin duplicar alertas.


def test_interpretacion_parcial_se_conserva_para_reintentar(tmp_path):
    info = publicar_evento(EVENTO, tmp_path)
    assert procesar_cola(tmp_path, Mock(return_value={"estado_ia": "parcial"})) == ["parcial"]
    assert (tmp_path / "cola_ia" / (info["id_evento"] + ".json")).exists()


def test_evento_invalido_se_aparta_de_la_cola(tmp_path):
    info = publicar_evento({"evento": "interrupcion_generacion", "inversor": 2}, tmp_path)
    assert procesar_cola(tmp_path, Mock(return_value={"estado_ia": "evento_invalido"})) == ["evento_invalido"]
    assert not (tmp_path / "cola_ia" / (info["id_evento"] + ".json")).exists()
    assert (tmp_path / "eventos_invalidos" / (info["id_evento"] + ".json")).exists()


def test_excepcion_del_agente_no_borra_evento(tmp_path):
    info = publicar_evento(EVENTO, tmp_path)
    fallo = Mock(side_effect=RuntimeError("Ollama detenido"))
    assert procesar_cola(tmp_path, fallo) == ["no_disponible"]
    assert (tmp_path / "cola_ia" / (info["id_evento"] + ".json")).exists()


def test_multiples_eventos_tienen_ids_distintos(tmp_path):
    a = publicar_evento(EVENTO, tmp_path)
    b = publicar_evento(EVENTO, tmp_path)
    assert a["id_evento"] != b["id_evento"]
    with (tmp_path / "alertas_anomalias.csv").open(encoding="utf-8") as f:
        assert len(list(csv.DictReader(f))) == 2


def test_encolar_sin_duplicar_csv_del_detector(tmp_path):
    info = encolar_evento(EVENTO, tmp_path)
    assert info["ia_encolada"] is True
    assert not (tmp_path / "alertas_anomalias.csv").exists()
    assert len(list((tmp_path / "cola_ia").glob("*.json"))) == 1
