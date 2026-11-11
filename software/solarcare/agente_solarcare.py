"""Agente de inteligencia artificial para SolarCare AI.

Sistema 1: Tev1 0.8B, a través de la API /v1/systemone compatible con Jev.
Sistema 2: Qwen3 1.7B, a través de Ollama.

El detector convencional registra las anomalías de manera independiente.
Este módulo únicamente las valida e interpreta; no controla los inversores.
"""

import json
import math
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ollama import Client


OLLAMA_URL = "http://127.0.0.1:11434"
MODELO_SISTEMA1 = "tev1:0.8b"
MODELO_SISTEMA2 = "qwen3:1.7b"
TIMEOUT_SEGUNDOS = 120


def consultar_tev1(evento):
    """Consulta Tev1 y devuelve una puntuación entre 0 y 1, o None si falla.

    La puntuación evalúa la pregunta de revisión técnica; no indica la
    probabilidad real de una falla eléctrica ni su gravedad confirmada.
    """
    solicitud = {
        "model": MODELO_SISTEMA1,
        "keep_alive": 0,  # Descargar el modelo de memoria al finalizar.
        "state": evento,
        "questions": {
            "requiere_revision": {
                "type": "noul",
                "instructions": (
                    "Does this detected event warrant technical review?"
                ),
            }
        },
    }

    datos = json.dumps(solicitud).encode("utf-8")
    peticion = Request(
        f"{OLLAMA_URL}/v1/systemone",
        data=datos,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(peticion, timeout=TIMEOUT_SEGUNDOS) as respuesta:
            resultado = json.load(respuesta)

        puntuacion = resultado["answers"]["requiere_revision"]["noul"]
        if (
            type(puntuacion) not in (int, float)
            or not math.isfinite(puntuacion)
            or not 0 <= puntuacion <= 1
        ):
            raise ValueError("Puntuación de Tev1 inválida")

        return float(puntuacion)

    except (HTTPError, URLError, TimeoutError, KeyError, ValueError, TypeError) as error:
        print(f"Error en Sistema 1: {error}")
        return None


def _descripcion_medida_transitoria(evento):
    """Construye una descripción basada en mediciones verificadas."""
    anterior = evento["potencia_anterior_w"]
    actual = evento["potencia_actual_w"]
    posterior = evento["potencia_recuperada_w"]

    corrientes = evento.get("corrientes_cc_a", [])
    tensiones = evento.get("tensiones_cc_v", [])

    texto_corrientes = ", ".join(
        f"{float(valor):g}" for valor in corrientes
    )
    texto_tensiones = ", ".join(
        f"{float(valor):g}" for valor in tensiones
    )

    ventana = evento.get(
        "duracion_maxima_minutos",
        evento["duracion_minutos"]
    )

    return (
        f"Inversor {evento['inversor']}: la potencia AC pasó de "
        f"{anterior:g} W a {actual:g} W y posteriormente "
        f"se registraron {posterior:g} W. "
        f"Durante la medición anómala, las corrientes CC fueron "
        f"[{texto_corrientes}] A y las tensiones CC fueron "
        f"[{texto_tensiones}] V. "
        f"La última generación previa se observó a las "
        f"{evento.get('ultima_generacion_previa', 'hora no indicada')}. "
        f"La medición anómala se registró a las "
        f"{evento['inicio_evento']} y la recuperación se observó a las "
        f"{evento.get('recuperacion_observada', 'hora no indicada')}. "
        f"Los {ventana:g} minutos representan únicamente una "
        f"cota superior basada en las mediciones. "
        f"No se conoce la duración exacta ni la causa del evento."
    )


def consultar_qwen(evento, puntuacion):
    """Solicita a Qwen una interpretación en JSON; devuelve None si falla."""
    datos = {
        "evento": evento,
        "puntuacion_revision_tev1": puntuacion,
    }

    instrucciones = """
    Eres un asistente técnico especializado en sistemas fotovoltaicos
    conectados a red. Recibirás un evento detectado por un algoritmo
    convencional y una puntuación auxiliar de Tev1 (que podría ser null).

    Devuelve exclusivamente un objeto JSON con estos campos:
    - explicacion: descripción breve de las mediciones del evento.
    - posibles_causas: lista de exactamente tres hipótesis técnicas.
    - recomendacion: revisión segura propuesta para personal autorizado.

    La puntuación de Tev1 no representa la probabilidad de falla eléctrica.
    Nunca conviertas esa puntuación en un diagnóstico ni en una gravedad
    confirmada. No inventes mediciones ni afirmes una causa confirmada.
    No sugieras manipular equipos energizados. Responde en español.
    """

    tipo_evento = evento.get("evento")

    if tipo_evento == "indisponibilidad_web":
        instrucciones += """
        El evento se refiere a la aplicación WEB del SESLAB.
        La web no responde, pero las mediciones siguen actualizándose.
        Esto NO demuestra que el inversor esté fallando.
        Considera únicamente hipótesis relacionadas con el servicio web,
        la conectividad de red o errores del software/configuración web.
        Recomienda revisar estado del servicio, registros y conectividad.
        No atribuyas el evento a paneles, inversor o conexiones eléctricas.
        """

    elif tipo_evento == "ausencia_datos":
        instrucciones += """
        El evento se refiere a la AUSENCIA DE NUEVAS MEDICIONES.
        No demuestra que se haya interrumpido la generación eléctrica.
        Considera adquisición de datos, comunicación con monitoreo y
        almacenamiento o actualización de los archivos CSV.
        No atribuyas la ausencia de datos al sombreado, irradiancia,
        suciedad ni a fallas eléctricas sin evidencia.
        Recomienda revisar marcas temporales, logs y comunicación.
        """

    elif tipo_evento == "interrupcion_generacion":
        instrucciones += """
        El evento corresponde a una posible INTERRUPCIÓN DE GENERACIÓN.
        Se informó de una disminución de potencia durante generación
        esperada y de que las mediciones siguen actualizándose.
        Considera como hipótesis la irradiancia, las protecciones o las
        alarmas/estados de operación del inversor; ninguna está confirmada.
        No confundas esto con ausencia de datos.
        No describas la puntuación de Tev1 como probabilidad de falla.
        Recomienda revisar historial de potencia, alarmas y mediciones
        de tensión y corriente CC, sin intervenciones energizadas.
        """

    elif tipo_evento == "reduccion_corriente_dc":
        instrucciones += """
        El evento se refiere a corriente en una ENTRADA CC monitoreada,
        que podría agrupar varias cadenas fotovoltaicas.
        Considera como hipótesis la irradiancia, el sombreado y las
        condiciones del campo FV, sin atribuir una causa confirmada.
        Recomienda revisar registros y datos disponibles y solicitar
        inspección segura únicamente a personal autorizado.
        No infieras fallos del control del inversor solo por este evento.
        """

    # CONTEXTO_TEMPORAL_SOLARCARE_V1
    if (
        tipo_evento == "interrupcion_generacion"
        and evento.get("subtipo") == "transitoria"
    ):
        instrucciones += """
        REGLAS ESPECIFICAS PARA INTERRUPCIONES TRANSITORIAS:

        1. inicio_evento representa la primera medicion anomala,
           NO el instante exacto en que comenzo la interrupcion.

        2. recuperacion_observada representa la primera medicion
           posterior donde se observo nuevamente generacion.

        3. duracion_maxima_minutos es una cota superior estimada
           entre mediciones con generacion. NO es la duracion
           exacta de la interrupcion.

        4. Describe la potencia antes, durante y despues.
           Si se proporcionan corrientes_cc_a y tensiones_cc_v,
           menciona su comportamiento con valores concretos.

        5. Una caida de corriente a cero con tensiones CC
           presentes puede ser compatible con una interrupcion
           momentanea de extraccion de potencia, pero NO confirma
           una desconexion, proteccion ni falla especifica.

        6. Distingue hechos observados de posibles causas.
           No inventes mediciones de irradiancia ni alarmas.

        7. No afirmes que el inversor estuvo desconectado durante
           un numero exacto de minutos.
        """

    elif evento.get("duracion_tipo") == "hasta_confirmacion":
        instrucciones += """
        duracion_minutos representa el tiempo observado hasta
        confirmar la anomalia, NO su duracion total.
        No afirmes que el evento termino en confirmado_en.
        """

    if tipo_evento == "reduccion_corriente_dc":
        instrucciones += """
        Identifica expresamente el numero de entrada_cc si existe.
        No confundas una reduccion localizada con una interrupcion
        completa del inversor. No supongas que las otras entradas
        presentan fallas si los datos no lo demuestran.
        """

    try:
        # Crear el cliente dentro del bloque de control de errores.
        cliente = Client(host=OLLAMA_URL, timeout=TIMEOUT_SEGUNDOS)

        # Sistema 2: llamada secuencial después de la consulta a Tev1.
        respuesta = cliente.chat(
            model=MODELO_SISTEMA2,
            messages=[
                {"role": "system", "content": instrucciones},
                {"role": "user", "content": json.dumps(datos, ensure_ascii=False)},
            ],
            format="json",
            think=False,
            keep_alive=0,  # Descargar Qwen de memoria tras responder.
            options={"temperature": 0},
        )

        resultado = json.loads(respuesta.message.content)

        # Validación de estructura: no garantiza la exactitud técnica.
        if not isinstance(resultado, dict):
            raise ValueError("La respuesta no es un objeto JSON")

        campos = ("explicacion", "posibles_causas", "recomendacion")
        if not all(campo in resultado for campo in campos):
            raise ValueError("Faltan campos en la respuesta")

        if (
            not isinstance(resultado["explicacion"], str)
            or not resultado["explicacion"].strip()
        ):
            raise ValueError("La explicación debe ser texto no vacío")

        causas = resultado["posibles_causas"]
        if not isinstance(causas, list) or len(causas) != 3:
            raise ValueError("Se requieren tres posibles causas")
        if not all(isinstance(causa, str) and causa.strip() for causa in causas):
            raise ValueError("Las causas deben ser textos no vacíos")

        if (
            not isinstance(resultado["recomendacion"], str)
            or not resultado["recomendacion"].strip()
        ):
            raise ValueError("La recomendación debe ser texto no vacío")

        if (
            tipo_evento == "interrupcion_generacion"
            and evento.get("subtipo") == "transitoria"
        ):
            resultado["explicacion"] = (
                _descripcion_medida_transitoria(evento)
            )

        return resultado

    except Exception as error:
        # Solo falla el enriquecimiento por IA; no se toca el detector.
        print(f"Error en Sistema 2: {error}")
        return None


def validar_evento(evento):
    """Verifica estructura y coherencia básica del evento.

    Devuelve (es_valido, mensaje). No verifica la existencia física de
    una anomalía: esa responsabilidad corresponde al detector convencional.
    """
    if not isinstance(evento, dict):
        return False, "El evento debe ser un diccionario"

    campos_por_evento = {
        "reduccion_corriente_dc": ["reduccion_porcentual", "generacion_esperada"],
        "indisponibilidad_web": [
            "aplicacion_web_disponible",
            "mediciones_actualizadas",
        ],
        "ausencia_datos": ["mediciones_actualizadas"],
        "interrupcion_generacion": [
            "potencia_anterior_w",
            "potencia_actual_w",
            "generacion_esperada",
            "mediciones_actualizadas",
        ],
    }

    tipo_evento = evento.get("evento")
    if tipo_evento not in campos_por_evento:
        return False, "Tipo de anomalía desconocido"

    campos = ["evento", "inversor", "duracion_minutos"]
    campos += campos_por_evento[tipo_evento]
    for campo in campos:
        if campo not in evento:
            return False, f"Falta el campo: {campo}"

    inversor = evento["inversor"]
    if type(inversor) is not int or inversor < 1:
        return False, "Número de inversor inválido"

    duracion = evento["duracion_minutos"]
    if type(duracion) not in (int, float):
        return False, "La duración debe ser numérica"
    if not 0 < duracion < float("inf"):
        return False, "La duración debe ser positiva y finita"

    campos_booleanos = (
        "generacion_esperada",
        "mediciones_actualizadas",
        "aplicacion_web_disponible",
    )
    for campo in campos_booleanos:
        if campo in evento and type(evento[campo]) is not bool:
            return False, f"Valor inválido en: {campo}"

    if tipo_evento == "reduccion_corriente_dc":
        reduccion = evento["reduccion_porcentual"]
        if type(reduccion) not in (int, float):
            return False, "Reducción no numérica"
        if not 0 <= reduccion <= 100:
            return False, "Porcentaje de reducción inválido"

    elif tipo_evento == "indisponibilidad_web":
        if evento["aplicacion_web_disponible"]:
            return False, "La aplicación web figura disponible"
        if not evento["mediciones_actualizadas"]:
            return False, "No se confirma actualización de datos"

    elif tipo_evento == "ausencia_datos":
        if evento["mediciones_actualizadas"]:
            return False, "Las mediciones figuran actualizadas"

    elif tipo_evento == "interrupcion_generacion":
        for campo in ("potencia_anterior_w", "potencia_actual_w"):
            valor = evento[campo]
            if type(valor) not in (int, float):
                return False, f"Potencia no numérica: {campo}"
            if not 0 <= valor < float("inf"):
                return False, f"Potencia inválida: {campo}"

        if not evento["generacion_esperada"]:
            return False, "No se esperaba generación"
        if not evento["mediciones_actualizadas"]:
            return False, "No hay mediciones actualizadas"

    return True, "Evento válido"


def analizar_evento(evento):
    """Valida el evento y coordina Tev1 y Qwen de forma secuencial.

    Devuelve un diccionario con evento, puntuación, interpretación y estado:
    completo, parcial, no_disponible o evento_invalido.
    """
    es_valido, mensaje = validar_evento(evento)
    if not es_valido:
        return {
            "evento": evento,
            "puntuacion_revision": None,
            "interpretacion": None,
            "estado_ia": "evento_invalido",
            "error": mensaje,
        }

    puntuacion = consultar_tev1(evento)
    interpretacion = consultar_qwen(evento, puntuacion)

    if puntuacion is not None and interpretacion is not None:
        estado = "completo"
    elif puntuacion is not None or interpretacion is not None:
        estado = "parcial"
    else:
        estado = "no_disponible"

    return {
        "evento": evento,
        "puntuacion_revision": puntuacion,
        "interpretacion": interpretacion,
        "estado_ia": estado,
    }
