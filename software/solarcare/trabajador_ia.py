"""Procesa eventos de la cola usando el agente SolarCare AI, en otro proceso.

Se ejecuta por separado del detector; sin conexión con Ollama, los
registros originales y la cola quedan intactos para reintentar después.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from puente_detector_ia import DIRECTORIO_SALIDAS


def _guardar_json_atomico(ruta, contenido):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    temporal = ruta.with_suffix(".tmp")
    with temporal.open("w", encoding="utf-8") as archivo:
        json.dump(contenido, archivo, indent=2, ensure_ascii=False,
                  allow_nan=False)
        archivo.flush()
        os.fsync(archivo.fileno())
    os.replace(temporal, ruta)


def procesar_cola(directorio=DIRECTORIO_SALIDAS, analizador=None):
    """Procesa una vez los eventos pendientes.

    En uso real importa `analizar_evento` del agente; en pytest se puede
    proporcionar un analizador simulado para no necesitar Ollama.
    """
    if analizador is None:
        # Importación diferida: el módulo detector no necesita importar IA.
        from agente_solarcare import analizar_evento
        analizador = analizar_evento

    directorio = Path(directorio)
    cola = directorio / "cola_ia"
    resultados = directorio / "resultados_ia"
    rechazados = directorio / "eventos_invalidos"

    if not cola.exists():
        print("No hay eventos pendientes.")
        return []

    resumen = []
    for ruta in sorted(cola.glob("*.json")):
        try:
            paquete = json.loads(ruta.read_text(encoding="utf-8"))
            identificador = paquete["id_evento"]
            evento = paquete["evento"]
        except (OSError, ValueError, KeyError, TypeError) as exc:
            print(f"AVISO: no se pudo leer {ruta.name}: {exc}")
            resumen.append("lectura_invalida")
            continue

        try:
            respuesta = analizador(evento)
            if not isinstance(respuesta, dict):
                raise ValueError("El agente no devolvió un diccionario")
        except Exception as exc:
            # Los errores del agente nunca eliminan el evento pendiente.
            respuesta = {
                "evento": evento,
                "puntuacion_revision": None,
                "interpretacion": None,
                "estado_ia": "no_disponible",
                "error": str(exc),
            }

        estado = respuesta.get("estado_ia", "no_disponible")
        contenido = {
            "id_evento": identificador,
            "procesado_utc": datetime.now(timezone.utc).isoformat(
                timespec="seconds"
            ),
            "resultado": respuesta,
        }
        try:
            _guardar_json_atomico(resultados / f"{identificador}.json",
                                  contenido)
            if estado == "completo":
                ruta.unlink()  # Solo cuando se guardó el resultado completo.
            elif estado == "evento_invalido":
                rechazados.mkdir(parents=True, exist_ok=True)
                os.replace(ruta, rechazados / ruta.name)
            # parcial y no_disponible: permanecen en la cola para reintentar.
        except OSError as exc:
            print(f"AVISO: no se pudo guardar el resultado {identificador}: {exc}")
            resumen.append("error_escritura")
            continue

        print(f"IA: evento {identificador[:8]} -> {estado}")
        resumen.append(estado)

    return resumen


if __name__ == "__main__":
    procesar_cola()
