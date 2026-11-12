from datetime import datetime, timedelta
from pathlib import Path

import pytest

from detector_solarcare import (
    Medicion,
    detectar_anomalias,
    leer_csv,
)

BASE = Path(__file__).resolve().parent
T0 = datetime(2026, 3, 11, 9, 6, 49)


def escenario(
    tensiones=(862, 849, 846, 849),
    salto=92,
    fecha=T0,
    potencia_final=46478,
):
    return [
        Medicion(
            fecha, 46804,
            (20.9, 20.7, 13.8, 13.6),
            (714, 682, 682, 685)
        ),
        Medicion(
            fecha + timedelta(seconds=salto),
            0,
            (0, 0, 0, 0),
            tensiones
        ),
        Medicion(
            fecha + timedelta(seconds=2 * salto),
            potencia_final,
            (21.2, 19.9, 13.4, 13.3),
            (707, 704, 702, 702)
        ),
    ]


def transitorios(datos):
    return [
        e for e in detectar_anomalias(datos)
        if e.get("subtipo") == "transitoria"
    ]


def test_detecta_transitorio():
    eventos = transitorios(escenario())

    assert len(eventos) == 1
    assert eventos[0]["inicio_evento"] == (
        "2026-03-11 09:08:21"
    )
    assert eventos[0]["duracion_es_cota_superior"] is True


def test_sin_tensiones_no_confirma():
    assert transitorios(
        escenario(tensiones=None)
    ) == []


def test_hueco_grande_no_confirma():
    assert transitorios(
        escenario(salto=400)
    ) == []


def test_sin_recuperacion_no_confirma():
    assert transitorios(
        escenario(potencia_final=500)
    ) == []


def test_fuera_de_horario_no_confirma():
    assert transitorios(
        escenario(fecha=datetime(2026, 3, 11, 17))
    ) == []


def test_dos_ceros_no_son_transitorio_simple():
    datos = escenario()

    datos.insert(
        2,
        Medicion(
            datos[1].instante + timedelta(seconds=30),
            0,
            (0, 0, 0, 0),
            (840, 840, 840, 840)
        )
    )

    datos[3] = Medicion(
        datos[1].instante + timedelta(seconds=92),
        47000,
        (21, 20, 14, 14),
        (707, 704, 702, 702)
    )

    assert transitorios(datos) == []


@pytest.mark.parametrize("archivo,horas", [
    (
        "Marzo 2026/2026-03-11.csv",
        ["2026-03-11 09:08:21"]
    ),
    (
        "Mayo 2026/2026-05-13.csv",
        ["2026-05-13 10:46:09"]
    ),
    (
        "Junio 2026/2026-06-07.csv",
        [
            "2026-06-07 12:50:42",
            "2026-06-07 13:02:58",
            "2026-06-07 13:48:56",
        ]
    ),
])
def test_anomalias_documentadas_seslab(archivo, horas):

    ruta = (
        BASE
        / "datos_historicos"
        / "Registro inversor 2(1)"
        / "Registro inversor 2"
        / archivo
    )

    if not ruta.is_file():
        pytest.skip("Datos históricos del SESLAB no disponibles localmente")

    mediciones = leer_csv(ruta)

    encontrados = {
        e["inicio_evento"]
        for e in transitorios(mediciones)
    }

    assert set(horas).issubset(encontrados)
