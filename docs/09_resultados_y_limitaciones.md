# Resultados, limitaciones y conclusiones preliminares — SolarCare AI

> **Fecha de corte:** 11 de noviembre de 2026.  
> **Documento base:** propuesta de diseño de SolarCare AI entregada en el curso Taller de Sistemas Embebidos del Instituto Tecnológico de Costa Rica.  
> **Fuentes de evidencia:** código y pruebas de la rama `feature/solarcare-python-dashboard`, integración publicada en `feature/solarcare-integracion`, resultados observados por el equipo durante el desarrollo en Ubuntu y comunicación del avance de acceso a la máquina virtual del SESLAB.  
> **Advertencia:** este documento describe los **resultados disponibles al corte**. No sustituye el informe de aceptación final del sistema embebido y deberá actualizarse con las pruebas efectuadas en Raspberry Pi 4.

## 1. Resumen ejecutivo del estado actual

SolarCare AI busca complementar, y no reemplazar, el sistema de monitoreo fotovoltaico existente del SESLAB. El desarrollo ha permitido construir en Python un detector convencional de anomalías, un mecanismo de registro y publicación de eventos, un trabajador desacoplado para procesamiento con IA y una interfaz web de consulta. En Ubuntu se ha observado la ejecución local de Tev1 y Qwen3 mediante Ollama y el funcionamiento del dashboard Flask con chat contextual.

El equipo también **reportó haber conseguido conexión con la máquina virtual del SESLAB y visualizar mediciones CSV recientes**, aunque con un retraso entre el instante de medición y su disponibilidad. Este resultado reduce el riesgo de acceso a la información, pero todavía no demuestra por sí mismo que Raspberry Pi lea automáticamente la fuente ni que todo el flujo funcione sobre Yocto.

La rama de integración de Verónica incorpora scripts y la interfaz al árbol de trabajo, junto con recetas, servicios `systemd` y almacenamiento previsto para Raspberry Pi 4. **La presencia de estos archivos no constituye evidencia de compilación de imagen, arranque ni operación integral**. El cierre del proyecto depende de esas verificaciones y de los criterios aún incompletos de la propuesta.

## 2. Resultados técnicos comprobados o reportados

La siguiente clasificación diferencia resultados observados de implementaciones que necesitan validación adicional.

| Área | Resultado disponible | Tipo de evidencia y alcance | Situación |
| --- | --- | --- | --- |
| Validación de CSV | Lector con comprobaciones de encabezados, fecha y valores eléctricos | Código y pruebas automatizadas en Ubuntu | **Implementado y probado localmente** |
| Interrupciones sostenidas | Identificación por potencia previa, umbral y persistencia temporal | Datos sintéticos y pruebas unitarias | **Implementado y probado localmente** |
| Interrupciones transitorias | Identificación de una caída breve entre muestras con recuperación y tensiones CC | Pruebas sintéticas y tres casos de CSV históricos disponibles localmente | **Implementado y probado localmente** |
| Reducción de corriente CC | Comparación con referencia propia por entrada y confirmación temporal | Pruebas unitarias de reducción aislada, simultánea y discontinuidad | **Implementado y probado localmente** |
| Ausencia de mediciones | Evaluación de antigüedad de la última muestra y seguimiento de recuperación | Siete pruebas automatizadas; umbral todavía provisional | **Implementado y probado localmente** |
| Alertas y cola | CSV de anomalías independiente, JSON pendientes y reintentos | Diez pruebas automatizadas de integración con analizador simulado | **Implementado y probado localmente** |
| Tev1 | Puntuación auxiliar de necesidad de revisión | Ejecución manual del modelo en Ubuntu | **Probado localmente; salida contractual parcial** |
| Qwen3 | Interpretación, hipótesis y recomendación en formato estructurado | Ejecución manual del modelo en Ubuntu | **Probado localmente; requiere validación técnica y embebida** |
| Dashboard Flask | Visualización de muestras, curva de potencia, historial y diagnóstico | Uso y revisión visual en Ubuntu | **Probado localmente; sin batería HTTP automatizada publicada** |
| Chat contextual | Preguntas sobre eventos usando evidencia original y Qwen3 | Uso manual en Ubuntu | **Probado localmente; sin prueba en Raspberry Pi** |
| Acceso a máquina virtual | Visualización de CSV recientes con retraso | **Resultado comunicado por el equipo** | **Conectividad lograda; falta protocolo y evidencia reproducible** |
| Integración Yocto | Capa, imagen, recetas, servicios y aplicación en rama de Verónica | Inspección de configuración publicada en GitHub | **Integración en desarrollo; no equivale a prueba en hardware** |

### 2.1. Resultado cuantitativo de pruebas automatizadas

El conjunto de cinco archivos de pruebas en [`software/tests/`](../software/tests/) produjo **39 casos aprobados** en Ubuntu, utilizando los archivos históricos del SESLAB disponibles localmente:

| Grupo de pruebas | Casos |
| --- | ---: |
| Detector eléctrico convencional | 12 |
| Interrupciones transitorias y casos históricos | 9 |
| Ausencia/recuperación de mediciones | 7 |
| Cambio automático de día | 1 |
| Registro de alertas, cola y tratamiento de fallos | 10 |
| **Total** | **39** |

En el grupo de transitorios, **3 casos dependen de CSV históricos no distribuidos**. Un clon sin esos archivos ejecuta esas pruebas como omitidas (`skipped`), no como aprobadas: con las mismas dependencias se esperan **36 aprobadas y 3 omitidas**.

**Límite del resultado:** 39 pruebas aprobadas significan que los casos automatizados previstos se comportaron según sus expectativas, **no** que todos los requisitos originales estén aceptados, que exista una tasa conocida de falsos positivos o que el sistema esté listo para operar de forma continua en Raspberry Pi.

Para consultar las entradas, funciones de prueba y criterios específicos, véase [08 — Pruebas y validación](08_pruebas_y_validacion.md).

### 2.2. Resultados del procesamiento con IA

La implementación separa dos tareas:

- **Detección convencional:** los umbrales y criterios temporales en Python generan el evento, independientemente de Ollama.
- **Enriquecimiento con IA:** Tev1 evalúa si el evento merece revisión; Qwen3 genera explicación, hipótesis y una recomendación para personal autorizado.

Esta separación permitió desarrollar escenarios de prueba donde el analizador **no responde**, responde parcialmente o devuelve un resultado completo. Las pruebas muestran que la alerta original puede permanecer almacenada, que la cola conserva eventos pendientes y que es posible reintentarlos.

La **puntuación de Tev1 no es una probabilidad validada de falla física**; la propuesta original exige además categoría y prioridad explícitas, por lo que RF-15 no está totalmente cumplido. La interpretación de Qwen3 se valida en estructura JSON, pero su corrección técnica **no se garantiza** mediante ese control de formato.

La inferencia real y el chat se probaron en Ubuntu. Aún faltan métricas verificables de tiempos, memoria y CPU ejecutando ambos modelos en la Raspberry Pi con la imagen definitiva.

### 2.3. Resultado de la interfaz de usuario

La versión 2 del dashboard permite consultar una fecha, observar potencia AC y mediciones CC, revisar una curva temporal, seleccionar anomalías, visualizar análisis guardados y conversar con Qwen3.

El componente también diferencia tres conceptos que suelen confundirse:

1. **Dato disponible:** existe un CSV que puede abrirse.
2. **Dato actualizado:** la marca temporal satisface un criterio explícito de frescura.
3. **Operación física normal del inversor:** requiere evidencia adicional; **no se deduce** de los dos puntos anteriores.

En la versión publicada, Flask indica la disponibilidad de los archivos pero **no confirma por sí solo la frescura**. Su refresco del navegador cada **25 segundos** no equivale a la frecuencia de adquisición ni corrige el retraso de los CSV.

La **energía estimada** se obtiene por integración de muestras de potencia, excluyendo huecos mayores de 15 minutos; no equivale a un dato de facturación o medición certificada.

### 2.4. Acceso a datos recientes del SESLAB

El equipo reportó que ya pudo conectarse a la máquina virtual y visualizar datos conforme aparecen los registros CSV. Es un avance tangible frente al riesgo de conectividad contemplado en la etapa de diseño.

Para convertirlo en evidencia formal falta registrar, sin exponer información restringida:

- Desde **qué equipo** se realizó la conexión.
- Protocolo, permisos y ruta lógica utilizados.
- Marcas de tiempo comparables de medición y de disponibilidad.
- Variación del retraso en varias observaciones.
- Lectura **sin modificación** de archivos fuente.
- Comportamiento ante desconexión y recuperación.

**No se considera demostrada aún la lectura automática desde Raspberry Pi** ni el procesamiento integral de esas mediciones mediante detector, cola, modelos y dashboard en el entorno embebido.

## 3. Evaluación de cumplimiento respecto a la propuesta original

La matriz de trazabilidad contiene **16 requisitos funcionales (RF)** y **8 no funcionales (RNF)**. El estado documentado es el siguiente:

| Estado de requisito | RF | RNF | Total | Proporción |
| --- | ---: | ---: | ---: | ---: |
| **Implementado y probado localmente en Ubuntu** | 11 | 3 | **14** | **58,3 %** |
| **Parcialmente cubierto** | 3 | 3 | **6** | **25,0 %** |
| **Pendiente de implementación o evidencia suficiente** | 2 | 2 | **4** | **16,7 %** |
| **Total** | **16** | **8** | **24** | **100 %** |

Estos porcentajes son **conteos de requisitos clasificados**, no una medida de avance ponderado del producto terminado. Los requisitos tienen distinta complejidad y algunos dependen de ejecutar todo el sistema en la plataforma final.

Una estimación informal compartida durante el desarrollo fue de **aproximadamente 70 % de avance general**. Esa cifra sirve únicamente como orientación de planificación, **no** como porcentaje académico de cumplimiento verificado ni de aceptación embebida. No se recomienda presentarla como indicador de validación en la entrega final.

**Fuente de detalle:** [02 — Matriz de trazabilidad](02_matriz_requerimientos.md). Cualquier modificación de estado deberá sustentarse con evidencia y, cuando corresponda, registrarse también allí.

## 4. Cumplimiento de objetivos

Se realiza una evaluación preliminar de los tres objetivos específicos definidos en la propuesta, sin modificar su alcance original.

| Objetivo de diseño | Avance identificado | Estado para cierre final |
| --- | --- | --- |
| **OE1. Adquisición y procesamiento sin reemplazar el monitoreo SESLAB** | Lectura y procesamiento local de CSV; el equipo consiguió acceso a registros recientes de la VM. | **Parcial:** falta demostrar acceso automático y no invasivo desde la plataforma final, con evidencia de lectura únicamente. |
| **OE2. Detección de eventos eléctricos y de disponibilidad** | Detector de interrupciones, reducciones CC y ausencia de datos probado localmente. | **Avanzado:** faltan calibración, aceptación integral y supervisión de disponibilidad web prevista en RF-06/RF-07. |
| **OE3. Integración de IA local sobre Linux creado con Yocto** | Modelos utilizados en Ubuntu y recetas/servicios preparados en GitHub. | **Parcial:** falta evidencia de inferencia, operación conjunta y recursos de Raspberry Pi. |

**Objetivo general:** el desarrollo aún **no se declara cumplido totalmente**, porque su formulación depende del funcionamiento demostrado del sistema embebido y de la relación con el monitoreo del SESLAB.

## 5. Principales decisiones de diseño y resultados asociados

| Decisión técnica | Problema que atiende | Evidencia o límite actual |
| --- | --- | --- |
| Reutilizar los CSV y la infraestructura del SESLAB | No sustituir un sistema existente ni duplicar adquisición | Acceso a VM reportado; fuente de solo lectura en Raspberry Pi pendiente |
| Separar detector de IA | No bloquear detección por latencia o falla de un modelo | Pruebas locales de publicación, cola y reintento |
| Emplear reglas con confirmación temporal | Evitar tratar muestras aisladas o huecos como fallas sostenidas | Pruebas unitarias positivas y negativas |
| Referencia histórica reciente por entrada CC | Evitar comparar directamente entradas con corrientes de referencia diferentes | Algoritmo local validado en casos sintéticos; calibración física pendiente |
| Guardar alerta antes de encolar IA | Preservar la evidencia aunque el análisis falle | Pruebas de integración con fallos simulados |
| Interpretaciones estructuradas de Qwen3 | Facilitar consulta de explicaciones e hipótesis | JSON validado; exactitud técnica de hipótesis no garantizada |
| Ejecutar Tev1 y Qwen3 secuencialmente | Intentar limitar presión de memoria | Estrategia implementada; beneficio cuantitativo no medido en Raspberry Pi |
| Incorporar Flask y chat | Facilitar la comprensión de eventos por parte de usuarios | Uso local observado; despliegue embebido y seguridad pendientes |

## 6. Limitaciones identificadas

### 6.1. Cobertura funcional incompleta

**RF-06 y RF-07.** El agente de IA reconoce un tipo de evento denominado `indisponibilidad_web`, pero el monitor publicado **no comprueba automáticamente la disponibilidad HTTP de la aplicación web original del SESLAB**, ni demuestra la correlación «web caída mientras CSV continúa actualizándose». Es un requisito distinto de detectar ausencia de nuevas mediciones.

**RF-01 y RF-03.** Se dispone de operación manual y supervisión automática a través de programas, pero no de un selector unificado. El monitor reinspecciona versiones de archivos y deduplica alertas, sin evidencia de un registro persistente de procesamiento individual por fila.

**RF-15.** Tev1 produce una puntuación auxiliar de revisión; no devuelve todavía una categoría y prioridad explícitas tal como exige el criterio de la propuesta.

### 6.2. Verificabilidad y configuración

**RNF-01.** Aunque los módulos abren archivos CSV en lectura, falta adjuntar una comparación **SHA-256** antes y después de una operación autorizada sobre la fuente real.

**RNF-04.** Los errores de lectura pueden mostrarse en terminal o journal, pero no está comprobado un registro persistente específico que satisfaga el criterio original.

**RNF-05.** Los umbrales principales de los algoritmos de detección están declarados como constantes Python; falta una configuración externa verificable que permita modificarlos sin editar el detector.

### 6.3. Dependencia de los datos y de condiciones físicas

La detección se basa en potencia, corriente, tensión y marcas temporales, **no** en una medición simultánea de irradiancia, temperatura del módulo, estado de alarmas del inversor o topología física confirmada de las entradas CC.

Por ello:

- Una caída de corriente no demuestra por sí sola sombreado, daño del módulo o desconexión de una cadena.
- Una interrupción transitoria observada entre muestras no revela su **duración física exacta**.
- Un CSV desactualizado no prueba automáticamente que la generación eléctrica se haya detenido.
- Una respuesta de Qwen3 puede plantear hipótesis pertinentes sin convertirlas en diagnósticos confirmados.

Los **umbrales y horarios** actuales son valores de implementación y prueba que deberán calibrarse con la operación real del SESLAB. No existe una evaluación publicada de sensibilidad, especificidad o tasa global de falsos positivos.

### 6.4. Retraso de actualización y continuidad operativa

La consulta de archivos recientes del SESLAB presenta retraso respecto a la hora de medición. Todavía no se dispone de una serie cuantitativa que permita describir su variación, de modo que no puede garantizarse que el umbral de **20 minutos** para ausencia de datos sea adecuado bajo todas las condiciones.

El ciclo de supervisión del monitor (configurado en 10 segundos) y el refresco del dashboard (25 segundos) **son frecuencias de consulta**, no de adquisición o de respuesta física del inversor.

Faltan observaciones prolongadas que incluyan reinicios, cambio de día, interrupciones de red, archivos parcialmente escritos y recuperación del servicio.

### 6.5. Riesgos de despliegue embebido

La rama `feature/solarcare-integracion` de Verónica incorpora las recetas, servicios y una copia de la interfaz; persisten comprobaciones como:

- Construcción reproducible de `solarcare-image` con binarios Ollama ARM64 disponibles.
- Instalación del paquete cliente Python `ollama` y de los modelos requeridos.
- Incorporación efectiva de Flask, plantillas y recursos estáticos a la imagen.
- Habilitación de las unidades de SolarCare y su operación tras reinicio.
- Acceso remoto autorizado a CSV mediante la ruta esperada.
- Unificación y persistencia de los directorios usados por detector, trabajador y dashboard.
- Medición de RAM, CPU, disco y latencia, incluyendo el caso de IA no disponible.

La existencia de configuración en GitHub **no garantiza** que una imagen haya compilado, arrancado o pasado una prueba final. La prueba en Raspberry Pi es la evidencia requerida para cerrar estos puntos.

### 6.6. Seguridad, datos institucionales y presentación

Flask se ha utilizado mediante su servidor de desarrollo y una dirección de loopback; no se ha presentado una configuración final de acceso remoto con autenticación, protección de red y servidor WSGI apropiado.

Los datos reales del SESLAB, direcciones IP privadas, rutas con información restringida, credenciales y pesos de modelos **no deben publicarse** en el repositorio sin autorización expresa. La documentación de resultados debería utilizar extractos anonimizados, datos sintéticos o evidencia aprobada.

## 7. Prioridades para completar la entrega

Se propone la siguiente priorización, basada en su impacto sobre los objetivos de la propuesta:

| Prioridad | Actividad pendiente | Evidencia de aceptación requerida |
| --- | --- | --- |
| **Crítica** | Arrancar imagen Yocto y ejecutar servicios esenciales en Raspberry Pi 4 | Log de compilación, identificación de imagen y estado de servicios |
| **Crítica** | Leer desde Raspberry Pi un CSV reciente de la VM en modo solo lectura | Procedimiento autorizado, marcas temporales y verificación de integridad |
| **Crítica** | Ejecutar evento → alerta → cola → Tev1/Qwen3 → resultado | Archivos correlacionados mediante `id_evento` y tiempos medidos |
| **Alta** | Integrar dashboard Flask en la imagen y consultarlo desde navegador autorizado | Página, API y chat sobre el dispositivo, sin exponer servicios innecesariamente |
| **Alta** | Medir respuesta y recursos | RAM, CPU, latencia y persistencia ante falla de IA |
| **Alta** | Implementar supervisión de la web original (RF-06/RF-07) | Caso controlado de web indisponible con CSV recientes |
| **Media-alta** | Completar RF-15, RNF-01, RNF-04 y RNF-05 | Esquema de prioridad, hashes, errores persistentes y configuración externa |
| **Media** | Ajustar umbrales y evaluar falsos positivos | Pruebas con condiciones reales y criterios de aceptación definidos |
| **Media** | Incorporar evidencias al repositorio | Fichas con fecha, entorno, entrada, procedimiento y resultado |

Las prioridades son una **propuesta de planificación**; la distribución final depende de la viabilidad técnica y de las indicaciones del profesor. Las pruebas no deben requerir manipular inversores o circuitos energizados sin permisos y personal capacitado.

## 8. Registro de resultados finales: pendiente de completar

La siguiente tabla debe actualizarse **únicamente cuando existan evidencias de ejecución**, utilizando la [plantilla de pruebas](evidencias/plantilla_registro_prueba.md).

| Entregable esperado | Estado documentado al corte | Referencia futura |
| --- | --- | --- |
| Imagen Yocto construida | No verificado mediante evidencia adjunta | Y-01, Y-02 |
| Raspberry Pi arrancando con esa imagen | No verificado mediante evidencia adjunta | Y-03 |
| Ollama/Tev1/Qwen3 operativos en Raspberry Pi | No verificado mediante evidencia adjunta | Y-04, Y-05 |
| Adquisición/lectura remota desde Raspberry Pi | No verificado mediante evidencia adjunta | Y-06 |
| Detector y alertas en Raspberry Pi | No verificado mediante evidencia adjunta | Y-07 |
| Trabajador y resultados IA en Raspberry Pi | No verificado mediante evidencia adjunta | Y-08 |
| Recuperación ante falla de IA | No verificado en la plataforma embebida | Y-09 |
| Dashboard accesible en red autorizada | No verificado en la plataforma embebida | Y-10 |
| Persistencia tras reinicio | No verificado en la plataforma embebida | Y-11 |
| Recursos y desempeño aceptables | Sin mediciones del dispositivo objetivo | Y-12 |

**Importante:** «No verificado mediante evidencia adjunta» no significa que Verónica no lo haya realizado; significa que **todavía no contamos con resultados suficientes para acreditarlo en este documento**.

## 9. Conclusiones preliminares

**Primera.** SolarCare AI dispone de una implementación local del procesamiento de CSV y la detección de anomalías que responde a una parte sustancial de los requisitos funcionales. Las reglas deterministas, la corroboración temporal y las pruebas automatizadas aportan una base reproducible para avanzar hacia la integración.

**Segunda.** La publicación separada de alertas y el procesamiento por cola permiten mantener el registro de eventos aun cuando la IA esté ausente o devuelva una respuesta incompleta. Este comportamiento se comprobó localmente con escenarios de prueba, pero debe demostrarse en el sistema embebido para cerrar su aceptación.

**Tercera.** La integración de Tev1, Qwen3 y Flask agrega herramientas de interpretación y consulta al monitoreo fotovoltaico. Las salidas de IA constituyen **apoyo para revisión**, no evidencia suficiente para diagnosticar causas físicas ni para confirmar el estado operativo del inversor.

**Cuarta.** La conexión lograda con la máquina virtual del SESLAB representa un avance relevante en acceso a datos recientes. Su retraso de actualización hace necesario medir la frescura de los archivos y evitar afirmaciones de «tiempo real» sin calificación.

**Quinta.** La principal condición pendiente para declarar completado el proyecto es verificar **la operación integral en Raspberry Pi con Linux generado mediante Yocto**. Deben documentarse la compilación, los servicios, la lectura autorizada, la ejecución de los modelos, la interfaz y el consumo de recursos antes de formular conclusiones definitivas.

Estas conclusiones son **preliminares**. La redacción final deberá actualizarse con los resultados de integración y la aceptación del profesor, sin ocultar limitaciones ni presentar pruebas futuras como realizadas.

---

**Documentación de soporte:** [Matriz de requisitos](02_matriz_requerimientos.md) · [Arquitectura](03_arquitectura_del_sistema.md) · [Detector](04_implementacion_del_detector.md) · [Agente de IA](05_integracion_inteligencia_artificial.md) · [Interfaz](06_interfaz_grafica.md) · [Yocto](07_integracion_yocto.md) · [Pruebas](08_pruebas_y_validacion.md) · [Índice](README.md).
