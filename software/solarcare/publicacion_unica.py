"""Evita registrar dos veces la misma anomalía."""

import csv
import fcntl
import json
from pathlib import Path

from puente_detector_ia import (
    DIRECTORIO_SALIDAS,
    publicar_evento,
    _encolar,
)

CAMPOS_CLAVE = (
    "inversor",
    "evento",
    "subtipo",
    "entrada_cc",
    "inicio_evento",
)


def _clave(evento):
    if not isinstance(evento, dict) or not evento.get("inicio_evento"):
        raise ValueError(
            "El evento necesita una fecha de inicio"
        )

    return tuple(
        evento.get(campo)
        for campo in CAMPOS_CLAVE
    )


def publicar_evento_unico(
    evento,
    directorio=DIRECTORIO_SALIDAS
):
    clave = _clave(evento)

    directorio = Path(directorio)
    directorio.mkdir(parents=True, exist_ok=True)

    bloqueo = directorio / ".publicacion.lock"

    with bloqueo.open("a+") as archivo_bloqueo:
        fcntl.flock(
            archivo_bloqueo.fileno(),
            fcntl.LOCK_EX
        )

        registro = directorio / "alertas_anomalias.csv"

        if registro.exists():

            with registro.open(
                encoding="utf-8",
                newline=""
            ) as archivo:

                for fila in csv.DictReader(archivo):
                    try:
                        anterior = json.loads(
                            fila["evento_json"]
                        )
                        coincide = (
                            _clave(anterior) == clave
                        )
                    except (
                        KeyError,
                        ValueError,
                        TypeError
                    ):
                        continue

                    if coincide:
                        identificador = fila["id_evento"]

                        cola = (
                            directorio / "cola_ia"
                            / f"{identificador}.json"
                        )

                        resultado = (
                            directorio / "resultados_ia"
                            / f"{identificador}.json"
                        )

                        estado_cola = {
                            "ia_encolada": cola.exists(),
                            "error_cola": None,
                        }

                        if (
                            not cola.exists()
                            and not resultado.exists()
                        ):
                            estado_cola = _encolar(
                                evento,
                                directorio,
                                identificador,
                                fila["registrado_utc"]
                            )

                        print(
                            "ALERTA ya registrada:",
                            identificador[:8]
                        )

                        return {
                            "id_evento": identificador,
                            "alerta_guardada": True,
                            "duplicado": True,
                            **estado_cola,
                        }

        nuevo = publicar_evento(
            evento,
            directorio
        )

        nuevo["duplicado"] = False
        return nuevo
