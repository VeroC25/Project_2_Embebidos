# SolarCare AI

Sistema embebido inteligente para la detección de anomalías y el apoyo al diagnóstico de sistemas fotovoltaicos.

**Instituto Tecnológico de Costa Rica**  
Escuela de Ingeniería Electrónica  
Curso: Taller de Sistemas Embebidos

## Descripción

SolarCare AI complementa el sistema de monitoreo existente del SESLAB mediante el análisis de mediciones eléctricas del inversor 2.

El sistema identifica comportamientos anómalos y utiliza modelos de inteligencia artificial ejecutados localmente para generar interpretaciones y recomendaciones técnicas.

## Arquitectura

El flujo principal es:

CSV de mediciones
→ Monitor
→ Detector de anomalías
→ Registro de alertas
→ Cola de procesamiento
→ Tev1
→ Qwen3
→ Resultados JSON
→ Interfaz web

## Componentes

### Detector y agente de IA

Ubicación: `software/solarcare/`

- `detector_solarcare.py`: detección de anomalías eléctricas.
- `monitor_diario_solarcare.py`: supervisión de los CSV diarios.
- `monitorear_csv_solarcare.py`: análisis de archivos CSV.
- `detectar_ausencia_datos.py`: detección de datos desactualizados.
- `eventos_ausencia_solarcare.py`: generación de eventos de ausencia.
- `seguimiento_estado_datos.py`: seguimiento de ausencia y recuperación.
- `puente_detector_ia.py`: registro y publicación de eventos.
- `publicacion_unica.py`: prevención de alertas duplicadas.
- `trabajador_ia.py`: procesamiento de eventos pendientes.
- `agente_solarcare.py`: integración con los modelos de IA.

### Modelos de inteligencia artificial

- Tev1 (`tev1:0.8b`): evaluación estructurada de eventos.
- Qwen3 (`qwen3:1.7b`): interpretación técnica, recomendaciones y conversación.

Ambos modelos se ejecutan localmente mediante Ollama.

### Interfaz gráfica

Ubicación: `software/interfaz_solarcare_v2/`

Aplicación web desarrollada con Flask, HTML, CSS y JavaScript.

Permite visualizar:

- Gráficos de generación fotovoltaica.
- Mediciones eléctricas de las entradas CC.
- Historial de anomalías.
- Interpretaciones de Tev1 y Qwen3.
- Asistente conversacional con Qwen3.

### Integración con Yocto

Ubicación: `yocto/meta-solarcare/`

Contiene las recetas y configuraciones del sistema operativo embebido.

La integración y validación en Raspberry Pi están pendientes.

## Pruebas

Ubicación: `software/tests/`

Para ejecutar las pruebas desde la raíz del repositorio:

```bash
PYTHONPATH="$PWD/software/solarcare" python3 -m pytest -q software/tests/
```

Se verificaron 39 pruebas satisfactoriamente en Ubuntu con los datos históricos disponibles localmente.

Tres casos dependen de registros históricos del SESLAB y se omiten cuando dichos archivos no están disponibles.

## Estado del proyecto

- Detector de anomalías: funcional en Ubuntu.
- Agente Tev1 y Qwen3: funcional en Ubuntu.
- Interfaz web: funcional en Ubuntu.
- Chat contextual: funcional en Ubuntu.
- Integración con Yocto: en desarrollo.
- Validación en Raspberry Pi: pendiente.
- Acceso automático a los CSV del SESLAB: pendiente.

## Consideraciones

Los CSV originales del SESLAB no deben modificarse.

Los modelos de Ollama y los datos históricos no se incluyen en el repositorio.

Las interpretaciones de IA son informativas y no constituyen diagnósticos definitivos de fallas.
