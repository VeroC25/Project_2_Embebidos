"""Convierte la ausencia de mediciones en un evento SolarCare AI."""


def crear_evento_ausencia(informe, inversor=2):
    if informe.get("estado") != "sin_actualizacion":
        return None

    ultima = informe["ultima_medicion"]
    minutos = float(informe["minutos_sin_mediciones"])
    umbral = float(informe["umbral_minutos"])

    if minutos <= umbral:
        return None

    return {
        "evento": "ausencia_datos",
        "inversor": inversor,
        "mediciones_actualizadas": False,
        "duracion_minutos": minutos,
        "duracion_tipo": "tiempo_desde_ultima_medicion",
        "ultima_medicion": ultima,
        "umbral_minutos": umbral,
        "inicio_evento": ultima,
        "referencia_inicio": "ultima_medicion_disponible",
    }
