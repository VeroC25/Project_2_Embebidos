"""Pruebas del detector; NO requieren Ollama ni CSV reales."""

import csv
from datetime import datetime, timedelta

import pytest

from detector_solarcare import (
    Medicion,
    detectar_anomalias,
    leer_csv,
    principales_intervalos,
)


def serie(inicio="2026-11-01 09:00:00", n=8, paso_segundos=90,
          potencia=12000, corrientes=(10, 10, 7, 7)):
    instante = datetime.strptime(inicio, "%Y-%m-%d %H:%M:%S")
    return [
        Medicion(instante + timedelta(seconds=i * paso_segundos),
                 float(potencia), tuple(float(v) for v in corrientes))
        for i in range(n)
    ]


def test_sin_anomalias_constantes():
    assert detectar_anomalias(serie()) == []


def test_cero_fuera_de_horario_no_genera_interrupcion():
    datos = serie("2026-11-01 17:00:00", potencia=0,
                  corrientes=(0, 0, 0, 0))
    assert detectar_anomalias(datos) == []


def test_interrupcion_sostenida_con_generacion_previa():
    datos = serie(n=8)
    t = datos[-1].instante
    datos += [
        Medicion(t + timedelta(seconds=90 * i), 0, (0, 0, 0, 0))
        for i in range(1, 7)
    ]
    eventos = detectar_anomalias(datos)
    interrupciones = [e for e in eventos if e["evento"] == "interrupcion_generacion"]
    assert len(interrupciones) == 1
    assert interrupciones[0]["potencia_anterior_w"] == 12000
    assert interrupciones[0]["duracion_minutos"] >= 5


def test_interrupcion_breve_no_genera_alarma():
    datos = serie(n=8)
    t = datos[-1].instante
    datos += [Medicion(t + timedelta(seconds=90 * i), 0, (0, 0, 0, 0))
              for i in range(1, 3)]
    assert detectar_anomalias(datos) == []


def test_caida_aislada_sostenida_corriente_cc():
    datos = serie(n=8)
    t = datos[-1].instante
    datos += [Medicion(t + timedelta(seconds=90 * i), 9000, (3, 10, 7, 7))
              for i in range(1, 7)]
    eventos = detectar_anomalias(datos)
    cc = [e for e in eventos if e["evento"] == "reduccion_corriente_dc"]
    assert len(cc) == 1
    assert cc[0]["entrada_cc"] == 1
    assert cc[0]["reduccion_porcentual"] == 70.0


def test_caida_conjunta_no_es_caida_aislada():
    datos = serie(n=8)
    t = datos[-1].instante
    datos += [Medicion(t + timedelta(seconds=90 * i), 3000, (3, 3, 2, 2))
              for i in range(1, 7)]
    assert not [e for e in detectar_anomalias(datos)
                if e["evento"] == "reduccion_corriente_dc"]


def test_hueco_no_confirma_caida_de_corriente():
    datos = serie(n=8)
    t = datos[-1].instante
    datos += [
        Medicion(t + timedelta(seconds=90), 9000, (3, 10, 7, 7)),
        Medicion(t + timedelta(minutes=12), 9000, (3, 10, 7, 7)),
    ]
    assert detectar_anomalias(datos) == []


def test_hueco_no_confirma_interrupcion():
    datos = serie(n=8)
    t = datos[-1].instante
    datos += [
        Medicion(t + timedelta(seconds=90), 0, (0, 0, 0, 0)),
        Medicion(t + timedelta(minutes=12), 0, (0, 0, 0, 0)),
    ]
    assert detectar_anomalias(datos) == []


def test_intervalos_sin_huecos():
    intervalo, huecos = principales_intervalos(serie())
    assert intervalo == 90
    assert huecos == 0


def test_csv_incompleto_falla_con_mensaje(tmp_path):
    ruta = tmp_path / "incompleto.csv"
    ruta.write_text("Last update time,AC output power(W)\n"
                    "2026-11-01 12:00:00,1000\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Columnas faltantes"):
        leer_csv(ruta)


def test_csv_valores_incorrectos_rechazados(tmp_path):
    ruta = tmp_path / "valores.csv"
    columnas = ["Last update time", "AC output power(W)"] + [
        f"DC current {i}(A)" for i in range(1, 5)
    ]
    with ruta.open("w", newline="", encoding="utf-8") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=columnas)
        escritor.writeheader()
        escritor.writerow(dict(zip(columnas, ["2026-11-01 12:00:00", "nan", "1", "1", "1", "1"])))
    with pytest.raises(ValueError, match="Registro inválido"):
        leer_csv(ruta)


def test_dos_eventos_separados_se_detectan():
    datos = serie(n=8)
    t = datos[-1].instante
    primer = [Medicion(t + timedelta(seconds=90 * i), 9000, (3, 10, 7, 7))
              for i in range(1, 7)]
    datos.extend(primer)
    t = datos[-1].instante
    datos.extend([Medicion(t + timedelta(seconds=90 * i), 12000, (10, 10, 7, 7))
                  for i in range(1, 8)])
    t = datos[-1].instante
    datos.extend([Medicion(t + timedelta(seconds=90 * i), 9000, (3, 10, 7, 7))
                  for i in range(1, 7)])
    cc = [e for e in detectar_anomalias(datos)
          if e["evento"] == "reduccion_corriente_dc"]
    assert len(cc) == 2
