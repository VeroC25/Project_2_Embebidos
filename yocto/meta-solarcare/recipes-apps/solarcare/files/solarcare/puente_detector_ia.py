"""Puente entre el detector convencional y el agente SolarCare AI.

El detector puede llamar publicar_evento(evento) SIN esperar a Tev1 o Qwen3.
Escribe un CSV nuevo de alertas y encola un JSON para el trabajador de IA.
No lee ni modifica los CSV originales del SESLAB.
"""

import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

DIRECTORIO_SALIDAS = Path(__file__).resolve().parent / "salidas"
CAMPOS_CSV = (
    "id_evento", "registrado_utc", "categoria", "inversor",
    "duracion_minutos", "evento_json",
)


def publicar_evento(evento, directorio=DIRECTORIO_SALIDAS):
    """Guarda la alerta y deja el evento preparado para IA.

    `evento` ya debe corresponder a una anomalía emitida por el detector.
    El guardado de alertas NO depende de Ollama.

    Devuelve información sobre el registro y el encolado.
    """
    if not isinstance(evento, dict):
        raise TypeError("El detector debe entregar un diccionario")

    directorio = Path(directorio)
    directorio.mkdir(parents=True, exist_ok=True)

    identificador = uuid4().hex
    instante = datetime.now(timezone.utc).isoformat(timespec="seconds")
    evento_json = json.dumps(evento, ensure_ascii=False, allow_nan=False)

    # Registrar PRIMERO la alerta sin consultar Ollama.
    archivo_csv = directorio / "alertas_anomalias.csv"
    nuevo = not archivo_csv.exists() or archivo_csv.stat().st_size == 0
    with archivo_csv.open("a", encoding="utf-8", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=CAMPOS_CSV)
        if nuevo:
            escritor.writeheader()
        escritor.writerow({
            "id_evento": identificador,
            "registrado_utc": instante,
            "categoria": evento.get("evento", ""),
            "inversor": evento.get("inversor", ""),
            "duracion_minutos": evento.get("duracion_minutos", ""),
            "evento_json": evento_json,
        })
        archivo.flush()
        os.fsync(archivo.fileno())

    print(f"ALERTA registrada: {evento.get('evento', 'sin_categoria')}"
          f" | ID: {identificador[:8]}")

    # La cola es independiente: si falla, la alerta YA está guardada.
    cola_info = _encolar(evento, directorio, identificador, instante)
    return {
        "id_evento": identificador,
        "alerta_guardada": True,
        **cola_info,
    }


def encolar_evento(evento, directorio=DIRECTORIO_SALIDAS):
    """Encola SIN escribir otra alerta CSV.

    Usar cuando el detector definitivo ya registra sus propias alertas.
    """
    if not isinstance(evento, dict):
        raise TypeError("El detector debe entregar un diccionario")
    identificador = uuid4().hex
    instante = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return {
        "id_evento": identificador,
        **_encolar(evento, Path(directorio), identificador, instante),
    }


def _encolar(evento, directorio, identificador, instante):
    cola = directorio / "cola_ia"
    temporal = cola / f".{identificador}.tmp"
    destino = cola / f"{identificador}.json"
    try:
        cola.mkdir(parents=True, exist_ok=True)
        paquete = {
            "id_evento": identificador,
            "registrado_utc": instante,
            "evento": evento,
        }
        with temporal.open("w", encoding="utf-8") as archivo:
            json.dump(paquete, archivo, ensure_ascii=False, indent=2,
                      allow_nan=False)
            archivo.flush()
            os.fsync(archivo.fileno())
        os.replace(temporal, destino)  # Publicación atómica.
        encolado = True
        error = None
    except OSError as exc:
        temporal.unlink(missing_ok=True)
        encolado = False
        error = str(exc)
        print(f"AVISO: no se pudo encolar IA: {error}")
    return {"ia_encolada": encolado, "error_cola": error}
