import csv
from datetime import datetime, timedelta, time
from pathlib import Path


def verificar_actualizacion(
    ruta,
    ahora=None,
    umbral_minutos=20
):
    """
    Comprueba la antigüedad de la última medición.

    No diagnostica fallas eléctricas.
    No modifica los CSV.
    """

    ruta = Path(ruta)
    ahora = ahora or datetime.now()

    # Horario provisional de supervisión.
    if not time(7, 0) <= ahora.time() <= time(18, 0):
        return {
            "estado": "fuera_de_horario",
            "detalle": "Fuera del horario de supervisión"
        }

    if not ruta.exists():
        return {
            "estado": "archivo_no_disponible",
            "detalle": "No se encontró el CSV esperado"
        }

    fechas = []

    with ruta.open(
        encoding="utf-8-sig",
        newline=""
    ) as archivo:

        lector = csv.DictReader(archivo)

        for fila in lector:
            try:
                fecha = datetime.strptime(
                    fila["Last update time"].strip(),
                    "%Y-%m-%d %H:%M:%S"
                )
                fechas.append(fecha)

            except (ValueError, TypeError, KeyError, AttributeError):
                continue

    if not fechas:
        return {
            "estado": "sin_mediciones",
            "detalle": "No existen mediciones válidas"
        }

    ultima = max(fechas)

    if ultima > ahora + timedelta(minutes=2):
        return {
            "estado": "fecha_inconsistente",
            "detalle": "La última medición tiene una fecha futura"
        }

    retraso = (ahora - ultima).total_seconds() / 60

    if retraso > umbral_minutos:
        estado = "sin_actualizacion"
    else:
        estado = "actualizado"

    return {
        "estado": estado,
        "ultima_medicion": ultima.isoformat(sep=" "),
        "minutos_sin_mediciones": round(retraso, 2),
        "umbral_minutos": umbral_minutos
    }
