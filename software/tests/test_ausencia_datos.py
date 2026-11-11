import csv
from datetime import datetime

from detectar_ausencia_datos import verificar_actualizacion


def crear_csv(ruta, fechas):
    with ruta.open("w", encoding="utf-8", newline="") as f:
        escritor = csv.writer(f)
        escritor.writerow(["Last update time"])

        for fecha in fechas:
            escritor.writerow([fecha])


def test_datos_actualizados(tmp_path):
    ruta = tmp_path / "mediciones.csv"
    crear_csv(ruta, ["2026-11-01 17:11:07"])

    resultado = verificar_actualizacion(
        ruta,
        ahora=datetime(2026, 11, 1, 17, 14)
    )

    assert resultado["estado"] == "actualizado"


def test_ausencia_de_datos(tmp_path):
    ruta = tmp_path / "mediciones.csv"
    crear_csv(ruta, ["2026-11-01 17:11:07"])

    resultado = verificar_actualizacion(
        ruta,
        ahora=datetime(2026, 11, 1, 17, 40)
    )

    assert resultado["estado"] == "sin_actualizacion"


def test_fuera_de_horario(tmp_path):
    ruta = tmp_path / "mediciones.csv"
    crear_csv(ruta, ["2026-11-01 17:11:07"])

    resultado = verificar_actualizacion(
        ruta,
        ahora=datetime(2026, 11, 1, 20, 0)
    )

    assert resultado["estado"] == "fuera_de_horario"


def test_archivo_no_disponible(tmp_path):
    ruta = tmp_path / "no_existe.csv"

    resultado = verificar_actualizacion(
        ruta,
        ahora=datetime(2026, 11, 1, 12, 0)
    )

    assert resultado["estado"] == "archivo_no_disponible"


def test_archivo_sin_mediciones(tmp_path):
    ruta = tmp_path / "vacio.csv"
    crear_csv(ruta, [])

    resultado = verificar_actualizacion(
        ruta,
        ahora=datetime(2026, 11, 1, 12, 0)
    )

    assert resultado["estado"] == "sin_mediciones"


def test_fecha_futura_incorrecta(tmp_path):
    ruta = tmp_path / "mediciones.csv"
    crear_csv(ruta, ["2026-11-01 12:10:00"])

    resultado = verificar_actualizacion(
        ruta,
        ahora=datetime(2026, 11, 1, 12, 0)
    )

    assert resultado["estado"] == "fecha_inconsistente"


def test_recuperacion_de_datos(tmp_path):
    ruta = tmp_path / "mediciones.csv"

    crear_csv(ruta, ["2026-11-01 11:00:00"])

    primera = verificar_actualizacion(
        ruta,
        ahora=datetime(2026, 11, 1, 12, 0)
    )

    assert primera["estado"] == "sin_actualizacion"

    # Simular llegada de una medición nueva.
    with ruta.open("a", encoding="utf-8") as f:
        f.write("2026-11-01 11:59:00\n")

    segunda = verificar_actualizacion(
        ruta,
        ahora=datetime(2026, 11, 1, 12, 0)
    )

    assert segunda["estado"] == "actualizado"
