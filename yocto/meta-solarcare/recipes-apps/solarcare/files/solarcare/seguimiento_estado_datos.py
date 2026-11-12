"""Seguimiento persistente de ausencia y recuperación de datos."""

import json
import os
from datetime import datetime
from pathlib import Path


def actualizar_estado(informe, archivo_estado):
    ruta = Path(archivo_estado)
    ruta.parent.mkdir(parents=True, exist_ok=True)

    if ruta.exists():
        anterior = json.loads(
            ruta.read_text(encoding="utf-8")
        )
    else:
        anterior = {
            "ausencia_activa": False,
            "ultima_medicion": None
        }

    estado = informe["estado"]
    ultima = informe.get("ultima_medicion")
    previa = anterior.get("ultima_medicion")

    ausencia_activa = anterior["ausencia_activa"]
    recuperacion = False

    if estado == "sin_actualizacion":
        ausencia_activa = True

    elif estado == "actualizado":
        if ausencia_activa and ultima and previa:
            recuperacion = (
                datetime.fromisoformat(ultima)
                > datetime.fromisoformat(previa)
            )

        if recuperacion or not ausencia_activa:
            ausencia_activa = False

    # Conservar la marca temporal más reciente conocida.
    if ultima and (not previa or ultima > previa):
        previa = ultima

    nuevo_estado = {
        "ausencia_activa": ausencia_activa,
        "ultima_medicion": previa
    }

    temporal = ruta.with_suffix(".tmp")

    temporal.write_text(
        json.dumps(nuevo_estado, indent=4),
        encoding="utf-8"
    )

    os.replace(temporal, ruta)

    if recuperacion:
        return {
            "evento": "recuperacion_datos",
            "ultima_medicion": ultima,
            "ausencia_recuperada": True
        }

    return None
