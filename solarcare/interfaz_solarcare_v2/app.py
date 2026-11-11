"""SolarCare AI · Dashboard v2 · tema claro.

Interfaz de solo lectura de CSV/alertas/resultados, con chat Qwen3
independiente del detector. No altera mediciones ni estados del inversor.
"""
from __future__ import annotations

import csv
import json
import math
import os
import re
import sys
from collections import deque
from datetime import datetime, date
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from flask import Flask, jsonify, render_template, request

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent
OUTPUTS = Path(os.getenv("SOLARCARE_SALIDAS", str(PROJECT / "salidas"))).expanduser().resolve()
SOURCE_CSV = os.getenv("SOLARCARE_CSV", "").strip()
SOURCE_ROOT = os.getenv("SOLARCARE_CSV_RAIZ", "").strip()
OLLAMA_URL = os.getenv("SOLARCARE_OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
CHAT_MODEL = os.getenv("SOLARCARE_CHAT_MODEL", "qwen3:1.7b")
PORT = int(os.getenv("SOLARCARE_PORT", "8091"))
# Habilitar datos simulados únicamente durante pruebas.
DEMO_ENABLED = os.getenv("SOLARCARE_DEMO", "0") == "1"
app = Flask(__name__, template_folder="templates", static_folder="static")
app.json.ensure_ascii = False

TITLES = {
    "interrupcion_generacion": "Interrupción de generación",
    "baja_corriente": "Baja corriente CC",
    "reduccion_corriente": "Reducción de corriente CC",
    "ausencia_datos": "Ausencia de mediciones",
    "recuperacion_datos": "Recuperación de mediciones",
}


def _safe_date(value: str | None) -> str | None:
    if not value:
        return None
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return None
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError:
        return None


def _date_of(timestamp) -> str | None:
    if timestamp is None:
        return None
    text = str(timestamp)
    match = re.match(r"\s*(\d{4}-\d{2}-\d{2})", text)
    return _safe_date(match.group(1)) if match else None


def _read_ai(event_id: str) -> dict:
    if not event_id or not re.fullmatch(r"[a-fA-F0-9-]{1,80}", event_id):
        return {}
    file = OUTPUTS / "resultados_ia" / f"{event_id}.json"
    if not file.is_file():
        return {}
    try:
        obj = json.loads(file.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError):
        return {}
    if not isinstance(obj, dict):
        return {}
    result = obj.get("resultado", obj)
    if not isinstance(result, dict):
        return {}
    interp = result.get("interpretacion") or {}
    if not isinstance(interp, dict):
        interp = {}
    causes = interp.get("posibles_causas", [])
    return {
        "estado_ia": str(result.get("estado_ia", "pendiente")),
        "puntuacion_revision": result.get("puntuacion_revision"),
        "explicacion": str(interp.get("explicacion") or ""),
        "causas": causes if isinstance(causes, list) else [],
        "recomendacion": str(interp.get("recomendacion") or ""),
    }


def _read_alerts(max_rows: int = 200) -> list[dict]:
    file = OUTPUTS / "alertas_anomalias.csv"
    if not file.is_file():
        return []
    try:
        with file.open(encoding="utf-8-sig", newline="") as f:
            rows = deque(csv.DictReader(f), maxlen=max_rows)
    except (OSError, UnicodeError, csv.Error):
        return []
    events = []
    for row in reversed(rows):
        try:
            detail = json.loads(row.get("evento_json") or "{}")
            if not isinstance(detail, dict):
                detail = {}
        except (ValueError, TypeError):
            detail = {}
        event_type = str(row.get("categoria") or detail.get("evento") or "anomalia")
        event_id = str(row.get("id_evento") or "")
        ai = _read_ai(event_id)
        events.append({
            "id": event_id,
            "tipo": event_type,
            "titulo": TITLES.get(event_type, event_type.replace("_", " ").capitalize()),
            "fecha": str(detail.get("inicio_evento") or row.get("registrado_utc") or "—"),
            "inversor": detail.get("inversor", row.get("inversor", "2")),
            "duracion": detail.get("duracion_maxima_minutos", detail.get("duracion_minutos")),
            "duracion_tipo": detail.get("duracion_tipo"),
            "mediciones": {k: v for k, v in detail.items() if k in (
                "potencia_anterior_w", "potencia_w", "potencia_posterior_w",
                "corrientes_a", "tensiones_v", "recuperacion_observada", "entrada_cc", "subtipo"
            )},
            "estado_ia": ai.get("estado_ia", "pendiente"),
            "puntuacion": ai.get("puntuacion_revision"),
            "explicacion": ai.get("explicacion", "El análisis de IA todavía no está disponible."),
            "causas": ai.get("causas", []),
            "recomendacion": ai.get("recomendacion", ""),
        })
    return events


def _csv_path(chosen_date: str | None) -> Path | None:
    if SOURCE_ROOT:
        day = chosen_date or date.today().isoformat()
        return (Path(SOURCE_ROOT).expanduser().resolve() / day / f"{day}.csv")
    return Path(SOURCE_CSV).expanduser().resolve() if SOURCE_CSV else None


def _read_csv_measurements(chosen_date: str | None = None) -> dict | None:
    """Use the existing SolarCare CSV reader without changing the original file."""
    file = _csv_path(chosen_date)
    if file is None:
        return None
    if not file.is_file():
        return {"error": "No se encontró un CSV para la fecha seleccionada.", "fuente": file.name}
    try:
        if str(PROJECT) not in sys.path:
            sys.path.insert(0, str(PROJECT))
        from detector_solarcare import leer_csv
        readings = leer_csv(file)
        if not readings:
            return {"error": "El CSV no contiene mediciones válidas.", "fuente": file.name}
        if chosen_date:
            readings = [r for r in readings if _date_of(r.instante) == chosen_date]
            if not readings:
                return {"error": "El CSV no contiene mediciones de esa fecha.", "fuente": file.name}
        readings.sort(key=lambda r: r.instante)
        last = readings[-1]
        series = []
        # Use the full day's range, downsampling only for rendering.
        step = max(1, math.ceil(len(readings) / 300))
        samples = readings[::step]
        if samples[-1] is not last:
            samples.append(last)
        for r in samples:
            dt = r.instante.isoformat(sep=" ") if isinstance(r.instante, datetime) else str(r.instante)
            series.append({"x": dt, "y": round(max(0.0, float(r.potencia_w)) / 1000, 3)})
        # Trapezoidal estimated energy, excluding unobserved gaps above 15 minutes.
        energy_kwh = 0.0
        skipped_gaps = 0
        for before, after in zip(readings, readings[1:]):
            interval_h = (after.instante - before.instante).total_seconds() / 3600
            if 0 < interval_h <= 0.25:
                energy_kwh += (max(float(before.potencia_w), 0) + max(float(after.potencia_w), 0)) / 2000 * interval_h
            else:
                skipped_gaps += 1
        timestamp = last.instante.isoformat(sep=" ") if isinstance(last.instante, datetime) else str(last.instante)
        currents = list(last.corrientes_a)
        volts = list(getattr(last, "tensiones_v", []) or [])
        # Compatibilidad con versiones anteriores del lector del detector,
        # cuyo objeto Medicion incluía corrientes pero no tensiones.
        # Las tensiones se leen directamente del mismo CSV, en modo lectura.
        if not volts:
            try:
                with file.open(encoding="utf-8-sig", newline="") as handle:
                    for row in csv.DictReader(handle):
                        raw_stamp = (row.get("Last update time") or "").strip()
                        try:
                            same_sample = datetime.strptime(raw_stamp, "%Y-%m-%d %H:%M:%S") == last.instante
                        except ValueError:
                            same_sample = False
                        if same_sample:
                            volts = [float(row[f"DC voltage {k}(V)"]) for k in range(1, 5)]
                            break
            except (OSError, ValueError, KeyError, UnicodeError, csv.Error):
                volts = []
        return {
            "potencia_kw": round(float(last.potencia_w) / 1000, 2),
            "ultima_medicion": timestamp,
            "corrientes": currents,
            "tensiones": volts,
            "tension_promedio": round(sum(volts) / len(volts), 2) if volts else None,
            "corriente_promedio": round(sum(currents) / len(currents), 2) if currents else None,
            "energia_estimada_kwh": round(energy_kwh, 2),
            "energia_parcial": bool(skipped_gaps),
            "serie": series,
            "fuente": file.name,
            "fecha": _date_of(last.instante),
        }
    except Exception as exc:
        # Important: errors must not be mistaken for normal inverter operation.
        return {"error": f"No se pudo leer el CSV ({type(exc).__name__}).", "fuente": file.name}


def _demo_payload() -> dict:
    # Only used when no alert and no CSV is configured: clearly marked demo.
    series = []
    for i in range(65):
        k = 3.5 + 52 * math.exp(-((i - 33) / 19) ** 2)
        k += 2.5 * math.sin(i * 1.32) * math.exp(-((i - 33) / 23) ** 2)
        if i == 24:
            k = 0
        minutes = 5 * 60 + 30 + i * 11
        series.append({"x": f"2026-11-01 {minutes//60:02d}:{minutes%60:02d}:00", "y": round(k, 2)})
    return {
        "modo": "demo", "fecha_activa": "2026-11-01", "nota": "DEMO: datos ilustrativos; no representan el estado actual del inversor.",
        "potencia_kw": 0.0, "ultima_medicion": "2026-11-01 17:09:35", "estado_datos": "Ejemplo de demostración",
        "tension_promedio": 533.1, "corriente_promedio": 8.4, "energia_estimada_kwh": None, "energia_parcial": True,
        "corrientes": [8.5, 8.3, 8.6, 8.4], "tensiones": [532.1, 534.1, 533.4, 532.5], "serie": series,
        "eventos": [{
            "id": "demo-20261101", "tipo": "interrupcion_generacion", "titulo": "Interrupción de generación",
            "fecha": "2026-11-01 09:54:00", "inversor": 2, "duracion": 3.07, "duracion_tipo": "cota_superior",
            "estado_ia": "completo", "puntuacion": 0.5542,
            "explicacion": "La potencia cayó hasta 0 W y después se recuperó. Este evento es ilustrativo; la duración exacta y la causa no están confirmadas.",
            "causas": ["Comportamiento transitorio del inversor (sin confirmar)."],
            "recomendacion": "Corroborar mediciones y registros de alarmas antes de emitir un diagnóstico.",
            "mediciones": {},
        }],
    }


def _dashboard(chosen_date: str | None = None) -> dict:
    alerts = _read_alerts()
    measurements = _read_csv_measurements(chosen_date)
    if DEMO_ENABLED and not alerts and measurements is None:
        data = _demo_payload()
        if chosen_date and chosen_date != data["fecha_activa"]:
            data.update({"fecha_activa": chosen_date, "serie": [], "eventos": [], "nota": "DEMO: sin información de la fecha elegida."})
        return data

    valid = bool(measurements and "error" not in measurements)
    source_date = measurements.get("fecha") if valid else None
    inferred_date = chosen_date or source_date or (_date_of(alerts[0]["fecha"]) if alerts else None)
    selected_events = [a for a in alerts if _date_of(a["fecha"]) == inferred_date] if inferred_date else alerts
    return {
        "modo": "local", "fecha_activa": inferred_date,
        "nota": "Archivos locales. La presencia de datos no confirma operación en vivo ni el estado físico del inversor.",
        "potencia_kw": measurements.get("potencia_kw") if valid else None,
        "ultima_medicion": measurements.get("ultima_medicion") if valid else None,
        "estado_datos": "CSV disponible · frescura no verificada" if valid else "Sin CSV disponible",
        "tension_promedio": measurements.get("tension_promedio") if valid else None,
        "corriente_promedio": measurements.get("corriente_promedio") if valid else None,
        "energia_estimada_kwh": measurements.get("energia_estimada_kwh") if valid else None,
        "energia_parcial": measurements.get("energia_parcial", False) if valid else False,
        "corrientes": measurements.get("corrientes", []) if valid else [],
        "tensiones": measurements.get("tensiones", []) if valid else [],
        "serie": measurements.get("serie", []) if valid else [],
        "eventos": selected_events,
        "aviso_csv": measurements.get("error") if measurements and not valid else None,
    }


@app.get("/")
def home():
    return render_template("index.html")


@app.get("/api/estado")
def state():
    provided = request.args.get("fecha", "").strip()
    if provided and not _safe_date(provided):
        return jsonify({"error": "La fecha debe tener el formato YYYY-MM-DD."}), 400
    return jsonify(_dashboard(_safe_date(provided)))


# SolarCare chat: evidencia técnica v2.2
# Solo se incorporan mediciones realmente disponibles y marcas temporales.
# Se descartan explicaciones previas de la IA: son hipótesis, no evidencia.
def _evidencia_registrada(event_id):
    if not isinstance(event_id, str) or not re.fullmatch(r"[a-fA-F0-9-]{1,80}", event_id):
        return {}
    file = OUTPUTS / "alertas_anomalias.csv"
    if not file.is_file():
        return {}
    try:
        with file.open(encoding="utf-8-sig", newline="") as handle:
            rows = deque(csv.DictReader(handle), maxlen=250)
        for row in reversed(rows):
            if row.get("id_evento") != event_id:
                continue
            detail = json.loads(row.get("evento_json") or "{}")
            if not isinstance(detail, dict):
                return {}
            # Lista blanca: hechos de la detección, no interpretaciones generativas.
            allowed = (
                "evento", "subtipo", "inversor", "entrada_cc", "inicio_evento", "fin_evento",
                "confirmado_en", "duracion_minutos", "duracion_maxima_minutos",
                "duracion_tipo", "potencia_anterior_w", "potencia_actual_w",
                "potencia_posterior_w", "potencia_w", "corrientes_a", "tensiones_v",
                "corriente_referencia_a", "corriente_medida_a", "reduccion_porcentual",
                "generacion_esperada", "recuperacion_observada", "mediciones_actualizadas",
                "ultima_medicion", "referencia_inicio", "umbral_minutos",
            )
            return {k: detail[k] for k in allowed if k in detail}
    except (OSError, UnicodeError, csv.Error, ValueError, TypeError):
        pass
    return {}


def _muestras_csv_del_evento(selected):
    """Devuelve muestras con marcas de tiempo, nunca inventa datos de la VM."""
    if not isinstance(selected, dict):
        return {"estado": "No hay evento seleccionado."}
    fecha = _date_of(selected.get("fecha"))
    if not fecha:
        return {"estado": "El evento no tiene fecha verificable."}
    file = _csv_path(fecha)
    if file is None or not file.is_file():
        return {"estado": "No hay CSV configurado o disponible para la fecha del evento."}
    try:
        if str(PROJECT) not in sys.path:
            sys.path.insert(0, str(PROJECT))
        from detector_solarcare import leer_csv
        samples = [r for r in leer_csv(file) if _date_of(r.instante) == fecha]
        instante = datetime.fromisoformat(str(selected.get("fecha")).replace("Z", "+00:00"))
        # No mezclar horarios tz-aware y naive; estos CSV usan hora local naive.
        if instante.tzinfo is not None:
            return {"estado": "Marca temporal con huso horario incompatible con CSV local."}
        samples.sort(key=lambda r: r.instante)
        if not samples:
            return {"estado": "No hay muestras válidas para el día del evento."}
        nearest_idx = min(range(len(samples)), key=lambda i: abs((samples[i].instante - instante).total_seconds()))
        nearest_delta = abs((samples[nearest_idx].instante - instante).total_seconds())
        if nearest_delta > 120:
            return {"estado": "CSV disponible, pero no hay mediciones a menos de 120 s del evento."}

        def fmt(sample):
            return {
                "instante": sample.instante.isoformat(sep=" "),
                "potencia_ac_w": round(float(sample.potencia_w), 2),
                "corrientes_cc_a": [round(float(v), 3) for v in sample.corrientes_a],
                "tensiones_cc_v": [round(float(v), 2) for v in getattr(sample, "tensiones_v", ())],
            }

        picked = []
        # Si la adquisición presenta huecos, no presentar puntos lejanos como vecinos.
        for i in (nearest_idx - 1, nearest_idx, nearest_idx + 1):
            if 0 <= i < len(samples) and abs((samples[i].instante - instante).total_seconds()) <= 240:
                picked.append(fmt(samples[i]))
        # Algunas versiones anteriores del detector no incluyen tensiones_v;
        # recuperarlas únicamente del mismo CSV y las mismas marcas temporales.
        if any(not p["tensiones_cc_v"] for p in picked):
            try:
                by_time = {p["instante"]: p for p in picked}
                with file.open(encoding="utf-8-sig", newline="") as source:
                    for row in csv.DictReader(source):
                        raw = (row.get("Last update time") or "").strip()
                        try:
                            stamp = datetime.strptime(raw, "%Y-%m-%d %H:%M:%S").isoformat(sep=" ")
                        except ValueError:
                            continue
                        if stamp in by_time and not by_time[stamp]["tensiones_cc_v"]:
                            try:
                                by_time[stamp]["tensiones_cc_v"] = [
                                    round(float(row[f"DC voltage {k}(V)"]), 2)
                                    for k in range(1, 5)
                                ]
                            except (ValueError, KeyError, TypeError):
                                pass
            except (OSError, UnicodeError, csv.Error):
                pass
        return {
            "estado": "Mediciones locales históricas; no representan valores actuales.",
            "segundos_entre_evento_y_muestra_mas_cercana": round(nearest_delta, 1),
            "muestras": picked,
        }
    except (ValueError, TypeError, OverflowError, OSError, ImportError, AttributeError):
        return {"estado": "No fue posible leer muestras comparables del CSV."}


@app.post("/api/chat")
def chat():
    """Send one bounded contextual question to local Qwen3 (without touching acquisition)."""
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "Solicitud JSON inválida."}), 400
    question = payload.get("pregunta")
    if not isinstance(question, str) or not question.strip() or len(question) > 1200:
        return jsonify({"error": "Escribí una pregunta de entre 1 y 1200 caracteres."}), 400
    selected_id = payload.get("id_evento")
    selected = next((a for a in _read_alerts() if a["id"] == selected_id), None)
    if DEMO_ENABLED and selected is None and selected_id == "demo-20261101" and not _read_alerts():
        selected = _demo_payload()["eventos"][0]
    history = payload.get("historial", [])
    messages = [{
        "role": "system",
        "content": (
            "Sos SolarCare AI, asistente técnico del inversor 2 del SESLAB. "
            "Respondé en español, máximo 150 palabras, con frases completas y unidades. "
            "Basate únicamente en las mediciones del resumen_inversor, la evidencia del detector ""y las muestras CSV proporcionadas en el contexto; ""no confundas ausencia de alertas registradas con ausencia de anomalías. ""Si estado_detector indica ejecución no verificada, aclaralo explícitamente. ""No afirmes que las mediciones son actuales o en vivo sin verificar su frescura. "
            "no presentes hipótesis de Qwen3 ni valores ausentes como hechos. "
            "Si preguntan qué mediciones respaldan un evento, indicá las magnitudes NUMÉRICAS presentes "
            "(potencia AC, corriente CC medida y de referencia, porcentaje, tensiones, fecha) sin inventar otras. "
            "El porcentaje calculado por el detector no demuestra una causa física. "
            "Distingí: 1) mediciones observadas; 2) evento detectado; 3) posibles causas NO confirmadas; "
            "4) datos faltantes para validar causa (por ejemplo irradiancia, alarmas, "
            "comparación de otras entradas CC y condiciones del inversor). "
            "Si no hay una variable, decí explícitamente que no está disponible. "
            "Si la pregunta nombra un tipo de evento distinto al seleccionado, aclaralo y pedí seleccionar el correcto. "
            "No afirmés operación en vivo, fallas físicas confirmadas o duración exacta cuando sea cota superior. "
            "La puntuación Tev1 no es probabilidad de falla calibrada. "
            "Nunca recomendés manipular equipos energizados; las inspecciones corresponden a personal autorizado. "
            "No ejecutás acciones de control sobre el inversor."
        ),
    }]
    if isinstance(history, list):
        for item in history[-6:]:
            if isinstance(item, dict) and item.get("role") in ("user", "assistant") and isinstance(item.get("content"), str):
                messages.append({"role": item["role"], "content": item["content"][:800]})
    # Validar la fecha solicitada antes de consultar las mediciones.
    fecha_solicitada = payload.get("fecha")
    if fecha_solicitada is not None and _safe_date(fecha_solicitada) != fecha_solicitada:
        return jsonify({"error": "Fecha inválida. Utilizá YYYY-MM-DD."}), 400

    # Reutilizar los datos del dashboard sin ejecutar el detector.
    estado = _dashboard(fecha_solicitada)
    resumen = {
        "fecha": estado.get("fecha_activa"),
        "ultima_medicion": estado.get("ultima_medicion"),
        "estado_datos": estado.get("estado_datos"),
        "potencia_ac_kw": estado.get("potencia_kw"),
        "tension_dc_promedio_v": estado.get("tension_promedio"),
        "corriente_dc_promedio_a": estado.get("corriente_promedio"),
        "tensiones_dc_v": estado.get("tensiones"),
        "corrientes_dc_a": estado.get("corrientes"),
        "energia_estimada_kwh": estado.get("energia_estimada_kwh"),
        "energia_parcial": estado.get("energia_parcial"),
        "cantidad_muestras_grafica": len(estado.get("serie", [])),
        "cantidad_alertas_registradas": len(estado.get("eventos", [])),
        "estado_detector": "Ejecución no verificada",
    }

    # Conservar la evidencia específica cuando existe un evento seleccionado.
    verified = _evidencia_registrada(selected_id) if selected else {}
    contexto_csv = _muestras_csv_del_evento(selected) if selected else {"estado": "Sin evento seleccionado."}
    context = {
        "resumen_inversor": resumen,
        "origen": "registros_locales_no_en_vivo",
        "evento_seleccionado": {
            "tipo": selected.get("tipo"),
            "fecha": selected.get("fecha"),
            "inversor": selected.get("inversor"),
            "duracion_reportada": selected.get("duracion"),
            "tipo_duracion": selected.get("duracion_tipo"),
            "tev1_puntuacion_no_calibrada": selected.get("puntuacion"),
        } if selected else "No hay evento seleccionado o no fue encontrado.",
        "evidencia_detector": verified if verified else "No hay campos crudos verificables del detector.",
        "muestras_csv": contexto_csv,
    }
    messages.append({
        "role": "user",
        "content": (
            "Datos disponibles (información local, NO estado en vivo). "
            "Las preguntas y respuestas anteriores no son evidencia de mediciones.\n"
            + json.dumps(context, ensure_ascii=False, default=str)[:6500]
            + "\n\nPregunta del usuario: " + question.strip()
        ),
    })
    body = json.dumps({
        "model": CHAT_MODEL, "messages": messages, "stream": False, "think": False, "keep_alive": 0,
        "options": {"temperature": 0.2, "num_predict": 600},
    }, ensure_ascii=False).encode("utf-8")
    req = Request(f"{OLLAMA_URL}/api/chat", data=body, method="POST", headers={"Content-Type": "application/json"})
    try:
        with urlopen(req, timeout=100) as reply:
            result = json.loads(reply.read(500_000).decode("utf-8"))
        answer = result.get("message", {}).get("content")
        if not isinstance(answer, str) or not answer.strip():
            return jsonify({"error": "Qwen3 no devolvió una respuesta legible."}), 502
        # Some reasoning models return <think>...</think>; do not expose hidden deliberation in UI.
        answer = re.sub(r"<think>.*?</think>", "", answer, flags=re.DOTALL).strip()
        if not answer:
            return jsonify({"error": "Qwen3 no devolvió una respuesta final."}), 502
        return jsonify({"respuesta": answer, "modelo": CHAT_MODEL})
    except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError, ValueError):
        return jsonify({"error": f"No fue posible consultar {CHAT_MODEL}. Comprobá que Ollama y el modelo estén disponibles en esta computadora."}), 503


if __name__ == "__main__":
    print("SolarCare AI | Dashboard v2 · tema claro")
    print(f"Abrí en Firefox: http://127.0.0.1:{PORT}")
    print("Datos locales de solo lectura; preguntas a Qwen3 mediante Ollama local.")
    app.run(host="127.0.0.1", port=PORT, debug=False)
