# Matriz de trazabilidad y estado de requerimientos — SolarCare AI

> **Estado de referencia:** 11 de noviembre de 2026.  
> **Documento base:** *SolarCare AI: propuesta de diseño de un sistema embebido inteligente para el análisis de anomalías fotovoltaicas*, entrega de diseño (sección IV, cuadros I y II).  
> **Alcance de esta revisión:** implementación Python y dashboard de la rama `feature/solarcare-python-dashboard`; infraestructura Yocto publicada en `main` y avances de la rama `feature/solarcare-integracion`.  
> **Importante:** esta matriz distingue funcionamiento comprobado en Ubuntu, implementación en el código y validación pendiente en Raspberry Pi. No equivale a una aceptación formal de todos los requisitos.

## Convenciones de estado

- **Implementado (Ubuntu):** la funcionalidad está presente en el código y se cuenta con pruebas locales pertinentes. Todavía puede requerir validación en el dispositivo final.
- **Parcial:** existe una implementación o avance comprobado, pero falta una parte del criterio de aceptación.
- **Pendiente:** no se identificó en el código publicado una implementación o evidencia suficiente del criterio.
- **Validación embebida pendiente:** incluso para requisitos implementados en Ubuntu, falta comprobar el comportamiento del conjunto en Raspberry Pi con la imagen Yocto, cuando aplique.

## 1. Requerimientos funcionales (RF)

| ID | Requerimiento abreviado del diseño | Estado | Implementación / evidencia existente | Brecha y verificación pendiente |
| --- | --- | --- | --- | --- |
| RF-01 | Seleccionar modo automático o manual | **Parcial** | Modo automático en [monitor_diario_solarcare.py](../software/solarcare/monitor_diario_solarcare.py); ejecución manual por ruta en [detector_solarcare.py](../software/solarcare/detector_solarcare.py). | Existen dos vías mediante terminal, no una selección unificada desde la interfaz de operación. |
| RF-02 | Consultar periódicamente una fuente configurada | **Implementado (Ubuntu)** | Monitor con `--continuo`, `--intervalo` y `--raiz` en [monitor_diario_solarcare.py](../software/solarcare/monitor_diario_solarcare.py). | Verificar ciclos y registros de ejecución conectados a la fuente remota. |
| RF-03 | Distinguir registros nuevos de repetidos | **Parcial** | Detecta cambios mediante tamaño y fecha de modificación del CSV; [publicacion_unica.py](../software/solarcare/publicacion_unica.py) evita publicar dos veces un mismo evento. | La deduplicación de eventos no equivale a registrar individualmente qué filas ya fueron procesadas. Validar actualización incremental. |
| RF-04 | Elegir manualmente un CSV para analizar | **Implementado (Ubuntu)** | Argumento posicional `csv` de [detector_solarcare.py](../software/solarcare/detector_solarcare.py) y `archivo` de [monitorear_csv_solarcare.py](../software/solarcare/monitorear_csv_solarcare.py). | Confirmar flujo manual previsto para uso final, especialmente desde la interfaz si se exige allí. |
| RF-05 | Validar campos requeridos del CSV | **Implementado (Ubuntu)** | [leer_csv](../software/solarcare/detector_solarcare.py) valida encabezados, valores y orden temporal; pruebas en [test_detector_solarcare.py](../software/tests/test_detector_solarcare.py). | Ejecutar casos con formatos reales adicionales. |
| RF-06 | Consultar disponibilidad de la aplicación web del SESLAB | **Pendiente** | El agente conoce el tipo de evento `indisponibilidad_web`, pero esto no constituye una consulta al servicio web. | Implementar comprobación de disponibilidad de la URL configurada; ensayar respuesta normal, falla y timeout. |
| RF-07 | Detectar web no disponible con CSV recientes | **Pendiente** | No se identificó una correlación implementada entre chequeo HTTP y frescura de datos. | Verificar simultáneamente web inaccesible y mediciones actualizadas; registrar evento diferenciado. |
| RF-08 | Detectar ausencia de nuevas mediciones | **Implementado (Ubuntu)** | [detectar_ausencia_datos.py](../software/solarcare/detectar_ausencia_datos.py), [eventos_ausencia_solarcare.py](../software/solarcare/eventos_ausencia_solarcare.py) y [seguimiento_estado_datos.py](../software/solarcare/seguimiento_estado_datos.py). Pruebas en [test_ausencia_datos.py](../software/tests/test_ausencia_datos.py). | Calibrar umbral de antigüedad con el retraso normal de la plataforma SESLAB y comprobar el comportamiento durante la conexión real. |
| RF-09 | Identificar interrupciones de generación durante horario esperado | **Implementado (Ubuntu)** | [detector_solarcare.py](../software/solarcare/detector_solarcare.py): interrupciones sostenidas y transitorias, umbrales y continuidad temporal. | Calibrar los criterios y revisar falsos positivos con datos recientes. |
| RF-10 | Evaluar corriente de entradas CC frente a referencias | **Implementado (Ubuntu)** | Cada entrada se compara con su mediana previa; corroboración con otras entradas en [detector_solarcare.py](../software/solarcare/detector_solarcare.py). | Confirmar topología física de las entradas y adecuación de las referencias. |
| RF-11 | Detectar reducciones sostenidas de corriente CC | **Implementado (Ubuntu)** | Umbral de reducción, confirmación temporal y estabilidad de otras entradas en [detector_solarcare.py](../software/solarcare/detector_solarcare.py). | Validar umbrales con escenarios reales y calibrados. |
| RF-12 | Crear registro estructurado de eventos | **Implementado (Ubuntu)** | Eventos de Python con evidencia eléctrica; identificador, instante de registro y categoría en [puente_detector_ia.py](../software/solarcare/puente_detector_ia.py). | Inspeccionar exportaciones reales tras la integración. |
| RF-13 | Mostrar alertas en terminal | **Implementado (Ubuntu)** | Mensajes `ALERTA registrada` en [puente_detector_ia.py](../software/solarcare/puente_detector_ia.py). | Comprobar salida del servicio en `journalctl` en Raspberry Pi. |
| RF-14 | Guardar CSV de anomalías independiente | **Implementado (Ubuntu)** | Generación de `salidas/alertas_anomalias.csv` en [puente_detector_ia.py](../software/solarcare/puente_detector_ia.py). | Comprobar escritura persistente y separación de la fuente SESLAB en el dispositivo final. |
| RF-15 | Clasificar y priorizar mediante Tev1 | **Parcial** | [agente_solarcare.py](../software/solarcare/agente_solarcare.py) consulta `tev1:0.8b` mediante la API `/v1/systemone` y obtiene `puntuacion_revision` entre 0 y 1. | El criterio original solicita **categoría y prioridad válidas**; la puntuación actual no equivale por sí sola a esos dos campos. Definir salida verificable o acordar ajuste de requisito. |
| RF-16 | Interpretar y recomendar mediante Qwen3 | **Implementado (Ubuntu)** | [agente_solarcare.py](../software/solarcare/agente_solarcare.py) genera explicación, hipótesis y recomendación con `qwen3:1.7b`; se probó localmente con eventos conocidos. | Documentar evidencias de respuestas y validar ejecución en Raspberry Pi; revisar coherencia técnica sin asumir diagnósticos confirmados. |

**Resumen RF:** 11 implementados en Ubuntu, 3 parciales y 2 pendientes.

## 2. Requerimientos no funcionales (RNF)

| ID | Requerimiento abreviado del diseño | Estado | Implementación / evidencia existente | Brecha y verificación pendiente |
| --- | --- | --- | --- | --- |
| RNF-01 | Acceso exclusivamente de lectura a CSV originales | **Parcial** | [detector_solarcare.py](../software/solarcare/detector_solarcare.py) abre archivos con modo `r`; las salidas se escriben en directorio aparte. | Ejecutar el criterio formal del diseño: comparar SHA-256 antes y después de procesar archivos originales o copias verificables. Configurar permisos de lectura para acceso remoto. |
| RNF-02 | Reportes fuera de la fuente de mediciones | **Implementado (Ubuntu)** | Alertas y resultados en `salidas/` independientes, mediante [puente_detector_ia.py](../software/solarcare/puente_detector_ia.py). | Confirmar rutas y persistencia configuradas en Yocto. |
| RNF-03 | Conservar hora y fecha originales de la evidencia | **Implementado (Ubuntu)** | Los eventos conservan `inicio_evento`, `primera_medicion_anomala` y marcas de confirmación; [detector_solarcare.py](../software/solarcare/detector_solarcare.py). | Comparar casos de salida con las filas originales del CSV. |
| RNF-04 | Registrar errores de lectura de archivos | **Pendiente** | Se imprimen mensajes de error en [monitor_diario_solarcare.py](../software/solarcare/monitor_diario_solarcare.py). | Definir y comprobar un **registro persistente** de errores, no solamente salida de terminal. |
| RNF-05 | Modificar umbrales sin editar código del detector | **Pendiente** | Los umbrales principales están declarados como constantes de [detector_solarcare.py](../software/solarcare/detector_solarcare.py). | Exponer parámetros mediante configuración externa o argumentos CLI y probar sus modificaciones. |
| RNF-06 | Detectar y registrar aunque falle la IA | **Implementado (Ubuntu)** | Separación detector–cola–trabajador en [puente_detector_ia.py](../software/solarcare/puente_detector_ia.py) y [trabajador_ia.py](../software/solarcare/trabajador_ia.py); pruebas en [test_integracion.py](../software/tests/test_integracion.py). | Repetir escenario con Ollama caído en Raspberry Pi y observar continuidad de alertas. |
| RNF-07 | Inferencia local sin servicios externos en plataforma embebida | **Parcial** | Tev1 y Qwen3 fueron ejecutados localmente con Ollama en Ubuntu. | Ejecutar ambos en Raspberry Pi con la imagen Yocto y comprobar funcionamiento sin Internet. |
| RNF-08 | Adecuación a RAM, CPU y tiempo de respuesta de Raspberry Pi | **Parcial** | El agente ejecuta Tev1 antes de Qwen y solicita descarga del primero después de su uso. | Registrar memoria máxima, CPU y latencias de ambos modelos en Raspberry Pi; verificar que el detector continúe operativo. |

**Resumen RNF:** 3 implementados en Ubuntu, 3 parciales y 2 pendientes.

## 3. Resultado consolidado

| Estado | RF | RNF | Total |
| --- | ---: | ---: | ---: |
| Implementado (Ubuntu) | 11 | 3 | **14** |
| Parcial | 3 | 3 | **6** |
| Pendiente | 2 | 2 | **4** |
| **Total** | **16** | **8** | **24** |

Este conteo describe **cumplimiento funcional local**; no representa un porcentaje acreditado de validación del sistema embebido ni sustituye las evidencias de aceptación final.

## 4. Evidencia de pruebas disponible

Los cinco archivos de pruebas automatizadas están en [software/tests](../software/tests/). En el entorno local Ubuntu se ejecutaron con resultado **39 passed** el 11 de noviembre de 2026, disponiendo de tres CSV históricos del SESLAB mediante enlace local. En un clon sin esos tres CSV, las pruebas históricas se omiten mediante `pytest.skip`.

Ejecutar desde la raíz del repositorio:

```bash
PYTHONPATH="$PWD/software/solarcare" python3 -m pytest -q software/tests/
```

Estas pruebas incluyen escenarios de detección, ausencia de datos, cambio de día, escritura de alertas y comportamiento de la cola ante fallos. Las pruebas con analizador simulado **no acreditan** por sí solas la ejecución de los modelos reales ni del sistema Yocto.

**Evidencia todavía por adjuntar al repositorio:** captura/log con comando y fecha, casos de prueba reproducibles, registros del funcionamiento con modelos reales y pruebas sobre Raspberry Pi.

## 5. Integración con la infraestructura SESLAB

El equipo **reportó haber establecido conexión con la máquina virtual** y visualizar registros CSV recientes mientras se actualizan, con retraso respecto a la medición. Este avance reduce el riesgo de acceso a los datos, pero por sí solo **no confirma**:

1. Que sea la Raspberry Pi la que accede automáticamente a la fuente.
2. Que el detector procese dichos CSV de forma continua desde esa conexión.
3. Que el acceso esté configurado y verificado exclusivamente en lectura.
4. Que la cadena completa CSV → detector → cola → Tev1/Qwen3 → dashboard haya sido demostrada sobre Yocto.

**Pendiente de documentar sin publicar credenciales ni IP privadas:** equipo desde el que se realizó la prueba, protocolo de acceso autorizado, ruta lógica de los CSV, mediciones de retraso con marcas de tiempo, comando o servicio de lectura, registros y capturas de la validación.

## 6. Ampliaciones respecto al diseño original

La versión implementada incluye una [interfaz Flask](../software/interfaz_solarcare_v2/README.md) para visualizar tendencias, mediciones, anomalías, resultados de IA y un chat contextual con Qwen3. Se trata de una ampliación de presentación e interacción que debe documentarse por separado: **Flask funcional en Ubuntu no significa que ya esté integrado en la imagen Yocto**.

## 7. Próximas evidencias de aceptación prioritarias

1. **Acceso remoto:** mostrar lectura de CSV reciente, retraso observado y preservación de la fuente.
2. **Cuarta categoría de eventos:** implementar y ensayar RF-06 y RF-07 (caída del servicio web mientras los datos se mantienen actualizados).
3. **Modelos embebidos:** validar Tev1 y Qwen3 en Raspberry Pi mediante Ollama, incluidos fallos de servicio.
4. **Servicios Yocto:** comprobar detector, trabajador programado, directorios persistentes y disponibilidad del dashboard si se incluye en la entrega.
5. **Cierre de criterios pendientes:** salida categórica/prioridad para RF-15, configuración externa de umbrales RNF-05, registro de errores RNF-04, pruebas SHA-256 RNF-01 y métricas RNF-08.

## 8. Criterio para actualizar esta matriz

Para cambiar un estado a «verificado en Raspberry Pi», adjuntar un caso de prueba con **requisito, condiciones previas, procedimiento, entradas, resultado esperado, resultado observado, fecha, plataforma y evidencia**. Evitar marcar como aprobado un requisito únicamente porque el módulo existe o porque se ejecutó una simulación.

No incluir en GitHub datos institucionales no autorizados, credenciales, modelos voluminosos ni directorios de resultados con información sensible.
