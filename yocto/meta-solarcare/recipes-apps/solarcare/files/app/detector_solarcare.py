"""Detector convencional de anomalías del inversor 2 de SolarCare AI.

Primera versión: analiza un CSV histórico LOCAL en modo de solo lectura.
Detecta posibles interrupciones de potencia y caídas aisladas de corriente CC.
No consulta Ollama y no modifica los CSV del SESLAB.

Los umbrales son configuraciones iniciales para pruebas, NO diagnósticos.
"""

import argparse
import csv
import math
import statistics
from collections import deque
from dataclasses import dataclass
from datetime import datetime, time
from pathlib import Path


CAMPOS = (
    "Last update time",
    "AC output power(W)",
    "DC current 1(A)",
    "DC current 2(A)",
    "DC current 3(A)",
    "DC current 4(A)",
)

# Configuración inicial conservadora. Calibrar con históricos y SESLAB.
HORA_INICIO = time(8, 0)
HORA_FIN = time(15, 30)
DURACION_MINIMA_MIN = 5
POTENCIA_PREVIA_MIN_W = 2000
POTENCIA_BAJA_W = 100
POTENCIA_TRANSITORIA_MIN_W = 3000
TENSION_TRANSITORIA_MIN_V = 400
CORRIENTE_TRANSITORIA_MAX_A = 0.1
CORRIENTE_REFERENCIA_MIN_A = 2.0
CAIDA_CORRIENTE_MIN_FRACCION = 0.50  # 50 % o más.
PARES_ESTABLES_MIN = 2  # Al menos dos de las otras tres entradas.
CAMBIO_MAX_OTRAS_FRACCION = 0.25
VENTANA_REFERENCIA = 5  # Mediana de cinco muestras anteriores.
HUECO_MAX_SEGUNDOS = 300  # No confirmar anomalías a través de huecos >5 min.


@dataclass(frozen=True)
class Medicion:
    instante: datetime
    potencia_w: float
    corrientes_a: tuple[float, float, float, float]
    tensiones_v: tuple[float, float, float, float] | None = None


def leer_csv(ruta):
    """Lee mediciones de un CSV histórico, sin escribir en el archivo."""
    mediciones = []
    with Path(ruta).open("r", encoding="utf-8-sig", newline="") as archivo:
        lector = csv.DictReader(archivo)
        if lector.fieldnames is None:
            raise ValueError("CSV vacío o sin encabezados")
        faltantes = [campo for campo in CAMPOS if campo not in lector.fieldnames]
        if faltantes:
            raise ValueError(f"Columnas faltantes: {faltantes}")

        for numero_linea, fila in enumerate(lector, start=2):
            try:
                instante = datetime.strptime(
                    fila[CAMPOS[0]].strip(), "%Y-%m-%d %H:%M:%S"
                )
                potencia = float(fila[CAMPOS[1]])
                corrientes = tuple(float(fila[campo]) for campo in CAMPOS[2:])
                campos_tension = [
                    f"DC voltage {i}(V)" for i in range(1, 5)
                ]

                hay_tensiones = [
                    c in lector.fieldnames
                    for c in campos_tension
                ]

                if any(hay_tensiones) and not all(hay_tensiones):
                    raise ValueError("Columnas de tension incompletas")

                tensiones = (
                    tuple(float(fila[c]) for c in campos_tension)
                    if all(hay_tensiones) else None
                )

                valores = (
                    potencia, *corrientes, *(tensiones or ())
                )
                if not all(math.isfinite(v) and v >= 0 for v in valores):
                    raise ValueError("valores negativos o no finitos")
            except (ValueError, TypeError, AttributeError) as error:
                raise ValueError(f"Registro inválido en línea {numero_linea}: {error}") from error
            if mediciones and instante <= mediciones[-1].instante:
                raise ValueError(f"Marcas temporales no crecientes en línea {numero_linea}")
            mediciones.append(
                Medicion(instante, potencia, corrientes, tensiones)
            )
    return mediciones


def es_horario_de_prueba(instante):
    """Ventana fija inicial, NO sustituye sensores de irradiancia."""
    return HORA_INICIO <= instante.time() <= HORA_FIN


def transcurrido_minutos(inicio, fin):
    return (fin - inicio).total_seconds() / 60.0


def detectar_anomalias(mediciones):
    """Devuelve eventos compatibles con el agente, sin consultar la IA."""
    eventos = []
    anteriores = deque(maxlen=VENTANA_REFERENCIA)
    caidas_pendientes = {}  # canal -> inicio y referencias congeladas
    parada_pendiente = None
    anterior = None

    for medicion in mediciones:
        t = medicion.instante

        # Un hueco de adquisición no es evidencia de continuidad de una
        # anomalía eléctrica. Descartamos referencias antiguas y eventos
        # pendientes hasta disponer de nuevas mediciones consecutivas.
        if (anterior is not None and
                (t - anterior.instante).total_seconds() > HUECO_MAX_SEGUNDOS):
            anteriores.clear()
            caidas_pendientes.clear()
            parada_pendiente = None
            anterior = None

        horario = es_horario_de_prueba(t)

        # Interrupción: se detecta solo tras generación previa y 5 min a 0 W.
        if not horario or medicion.potencia_w > POTENCIA_BAJA_W:
            parada_pendiente = None
        elif parada_pendiente is None:
            if anterior and anterior.potencia_w >= POTENCIA_PREVIA_MIN_W:
                parada_pendiente = {
                    "inicio": t,
                    "potencia_previa": anterior.potencia_w,
                    "reportada": False,
                }
        elif (
            not parada_pendiente["reportada"]
            and transcurrido_minutos(parada_pendiente["inicio"], t)
            >= DURACION_MINIMA_MIN
        ):
            eventos.append({
                "evento": "interrupcion_generacion",
                "inversor": 2,
                "potencia_anterior_w": parada_pendiente["potencia_previa"],
                "potencia_actual_w": medicion.potencia_w,
                "duracion_minutos": round(
                    transcurrido_minutos(parada_pendiente["inicio"], t), 2
                ),
                "generacion_esperada": True,
                "mediciones_actualizadas": True,
                "inicio_evento": parada_pendiente["inicio"].isoformat(sep=" "),
                "fin_evento": t.isoformat(sep=" "),
            })
            parada_pendiente["reportada"] = True

        # Corrientes: cada entrada se compara con SU propia mediana previa;
        # solo marcamos una caída aislada si al menos dos pares siguen estables.
        referencias = None
        if len(anteriores) == VENTANA_REFERENCIA:
            referencias = tuple(
                statistics.median(r.corrientes_a[i] for r in anteriores)
                for i in range(4)
            )

        for canal, actual in enumerate(medicion.corrientes_a):
            pendiente = caidas_pendientes.get(canal)
            if not horario:
                caidas_pendientes.pop(canal, None)
                continue

            if pendiente is None:
                if referencias is None:
                    continue
                referencia = referencias[canal]
                if referencia < CORRIENTE_REFERENCIA_MIN_A:
                    continue
                if actual > referencia * (1 - CAIDA_CORRIENTE_MIN_FRACCION):
                    continue
                base_pares = referencias
                inicio = t
                pendiente = {
                    "inicio": inicio,
                    "referencia": referencia,
                    "bases_pares": base_pares,
                    "reportada": False,
                }
                caidas_pendientes[canal] = pendiente

            referencia = pendiente["referencia"]
            pares_estables = sum(
                1
                for otro in range(4)
                if otro != canal
                and pendiente["bases_pares"][otro] >= CORRIENTE_REFERENCIA_MIN_A
                and medicion.corrientes_a[otro]
                >= pendiente["bases_pares"][otro] * (1 - CAMBIO_MAX_OTRAS_FRACCION)
            )
            if (
                actual > referencia * (1 - CAIDA_CORRIENTE_MIN_FRACCION)
                or pares_estables < PARES_ESTABLES_MIN
            ):
                caidas_pendientes.pop(canal, None)
                continue

            duracion = transcurrido_minutos(pendiente["inicio"], t)
            if duracion >= DURACION_MINIMA_MIN and not pendiente["reportada"]:
                eventos.append({
                    "evento": "reduccion_corriente_dc",
                    "inversor": 2,
                    "entrada_cc": canal + 1,
                    "corriente_referencia_a": round(referencia, 3),
                    "corriente_medida_a": round(actual, 3),
                    "reduccion_porcentual": round(100 * (1 - actual / referencia), 2),
                    "duracion_minutos": round(duracion, 2),
                    "generacion_esperada": True,
                    "inicio_evento": pendiente["inicio"].isoformat(sep=" "),
                    "fin_evento": t.isoformat(sep=" "),
                })
                pendiente["reportada"] = True

        anteriores.append(medicion)
        anterior = medicion

    eventos.extend(detectar_transitorios(mediciones))

    for evento in eventos:
        evento["primera_medicion_anomala"] = evento["inicio_evento"]

        if evento.get("subtipo") == "transitoria":
            evento["duracion_tipo"] = "cota_superior"
            evento["duracion_maxima_minutos"] = evento["duracion_minutos"]
            evento.pop("fin_evento", None)

        else:
            evento["duracion_tipo"] = "hasta_confirmacion"
            evento["duracion_hasta_confirmacion_minutos"] = evento["duracion_minutos"]
            evento["confirmado_en"] = evento.pop("fin_evento", None)

    return sorted(
        eventos,
        key=lambda evento: evento["inicio_evento"]
    )


def detectar_transitorios(mediciones):
    """Detecta interrupciones breves con recuperacion observada."""

    eventos = []

    for antes, actual, despues in zip(
        mediciones,
        mediciones[1:],
        mediciones[2:]
    ):
        mismo_dia = (
            antes.instante.date()
            == actual.instante.date()
            == despues.instante.date()
        )

        intervalo_1 = (
            actual.instante - antes.instante
        ).total_seconds()

        intervalo_2 = (
            despues.instante - actual.instante
        ).total_seconds()

        if not (
            mismo_dia
            and es_horario_de_prueba(actual.instante)
            and 0 < intervalo_1 <= HUECO_MAX_SEGUNDOS
            and 0 < intervalo_2 <= HUECO_MAX_SEGUNDOS
            and antes.potencia_w > POTENCIA_TRANSITORIA_MIN_W
            and despues.potencia_w > POTENCIA_TRANSITORIA_MIN_W
            and actual.potencia_w <= POTENCIA_BAJA_W
            and all(
                i <= CORRIENTE_TRANSITORIA_MAX_A
                for i in actual.corrientes_a
            )
            and actual.tensiones_v is not None
            and all(
                v > TENSION_TRANSITORIA_MIN_V
                for v in actual.tensiones_v
            )
        ):
            continue

        # La duracion real es desconocida.
        # La ventana entre las mediciones con generacion
        # constituye una cota superior de la interrupcion.
        ventana_maxima = transcurrido_minutos(
            antes.instante,
            despues.instante
        )

        evento = {
            "evento": "interrupcion_generacion",
            "subtipo": "transitoria",
            "inversor": 2,
            "potencia_anterior_w": antes.potencia_w,
            "potencia_actual_w": actual.potencia_w,
            "potencia_recuperada_w": despues.potencia_w,
            "corrientes_cc_a": list(actual.corrientes_a),
            "tensiones_cc_v": list(actual.tensiones_v),
            "duracion_minutos": round(ventana_maxima, 2),
            "duracion_es_cota_superior": True,
            "generacion_esperada": True,
            "mediciones_actualizadas": True,
            "inicio_evento": actual.instante.isoformat(sep=" "),
            "fin_evento": despues.instante.isoformat(sep=" "),
            "ultima_generacion_previa": antes.instante.isoformat(
                sep=" "
            ),
            "recuperacion_observada": despues.instante.isoformat(
                sep=" "
            ),
        }

        eventos.append(evento)

    return eventos


def principales_intervalos(mediciones):
    """Información de calidad de datos; NO equivale a ausencia en vivo."""
    if len(mediciones) < 2:
        return None, 0
    segundos = [
        (b.instante - a.instante).total_seconds()
        for a, b in zip(mediciones, mediciones[1:])
    ]
    mediana = statistics.median(segundos)
    return mediana, sum(seg > 3 * mediana for seg in segundos)


def main():
    parser = argparse.ArgumentParser(description="Detector local inversor 2")
    parser.add_argument("csv", help="Ruta del CSV original o de su copia")
    parser.add_argument(
        "--publicar", action="store_true",
        help="Publicar anomalías detectadas en el puente de IA (opcional)",
    )
    args = parser.parse_args()

    mediciones = leer_csv(args.csv)
    intervalo, huecos = principales_intervalos(mediciones)
    eventos = detectar_anomalias(mediciones)

    print(f"Registros leídos: {len(mediciones)}")
    if mediciones:
        print(f"Desde: {mediciones[0].instante}")
        print(f"Hasta: {mediciones[-1].instante}")
    print(f"Intervalo mediano: {intervalo} segundos; huecos >3x: {huecos}")
    print(f"Posibles anomalías eléctricas: {len(eventos)}")
    for evento in eventos:
        print(
            f"- {evento['evento']} | {evento.get('inicio_evento')}"
            f" | entrada CC: {evento.get('entrada_cc', '-') }"
        )

    if args.publicar:
        # Importación condicional: podemos analizar sin el puente instalado.
        from publicacion_unica import publicar_evento_unico

        nuevas = 0
        duplicadas = 0

        for evento in eventos:
            resultado = publicar_evento_unico(evento)

            if resultado["duplicado"]:
                duplicadas += 1
            else:
                nuevas += 1

        print(
            f"Alertas nuevas: {nuevas}; "
            f"ya registradas: {duplicadas}"
        )
    else:
        print("Modo de inspección: NO se generaron alertas ni se ejecutó la IA.")


if __name__ == "__main__":
    main()
