# Pruebas y validación — SolarCare AI

> **Versión documental:** 11 de noviembre de 2026.  
> **Base de evaluación:** código y pruebas publicados en la rama `feature/solarcare-python-dashboard`, resultados de terminal observados durante el desarrollo en Ubuntu y avances comunicados por el equipo.  
> **Alcance:** se separa lo **comprobado localmente**, lo **reportado por el equipo** y lo **pendiente de validar en Raspberry Pi con Yocto**. Los pasos de las secciones futuras son un **plan de pruebas**, no resultados ejecutados.

## 1. Objetivos de la verificación

La estrategia de pruebas busca aportar evidencia de que SolarCare AI:

1. Lee y valida CSV sin alterar los registros originales del SESLAB.
2. Identifica eventos eléctricos mediante criterios deterministas y temporales.
3. Reconoce ausencia y recuperación de nuevas mediciones sin atribuir automáticamente una falla eléctrica.
4. Registra alertas de forma independiente de los modelos de IA y conserva los eventos pendientes.
5. Permite procesar eventos con Tev1 y Qwen3 localmente, validando la estructura de los resultados.
6. Muestra datos, alertas y análisis en la interfaz Flask sin presentar archivos históricos como telemetría en vivo.
7. Puede ejecutarse finalmente en Raspberry Pi 4 con Linux generado por Yocto, incluyendo servicios, almacenamiento y acceso autorizado a la VM.

Los puntos 1–4 cuentan con pruebas automatizadas locales; los puntos 5–6 tienen pruebas de uso manual en Ubuntu, pero su evidencia formal todavía debe adjuntarse al repositorio; el punto 7 sigue pendiente de resultados del dispositivo objetivo.

## 2. Entornos y grados de evidencia

| Entorno / fuente | Evidencia disponible | Limitación |
| --- | --- | --- |
| **Ubuntu, entorno virtual Python** | Ejecución de los cinco archivos de pruebas; salida **`39 passed`** comunicada en terminal el 11/11/2026, usando tres CSV históricos disponibles localmente. | No hay log original ni informe JUnit todavía comprometido en el repositorio. |
| **Ubuntu + Ollama** | Ejecución manual del agente con Tev1 y Qwen3, obtención de puntuaciones, interpretaciones y respuestas de chat. | Falta conservar entradas anonimizadas, salidas verificadas, versiones de modelos y tiempos medidos. |
| **Ubuntu + Flask** | Apertura local de la interfaz v2; visualización de mediciones y resultados y conversación contextual con Qwen3. | No hay suite automatizada publicada de rutas HTTP ni evidencia de despliegue remoto. |
| **Infraestructura SESLAB / VM** | El equipo **reportó conexión a la VM y visualización de CSV recientes**, con retraso respecto a la medición. | Falta acta de prueba reproducible, protocolo de acceso, equipo origen y medición sistemática del retraso. |
| **Raspberry Pi 4 + imagen Yocto** | Recetas, servicios y mecanismos de integración presentes en la rama de Verónica. | No se ha aportado evidencia verificable del flujo integral, recursos o tiempos de inferencia en el hardware. |

**Criterio de redacción:** un archivo de configuración en GitHub demuestra que la funcionalidad está **definida**; un test con datos sintéticos demuestra el comportamiento en ese escenario; una prueba con hardware y registros fechados demuestra la ejecución **en ese dispositivo**. Estas evidencias no son intercambiables.

## 3. Pruebas automatizadas en Ubuntu

### 3.1. Herramientas y comando de ejecución

El proyecto utiliza **pytest** y, cuando corresponde, herramientas de pruebas estándar de Python como `unittest.mock.Mock`, `unittest.mock.patch` y el directorio temporal `tmp_path` de pytest.

Desde la raíz del repositorio:

```bash
PYTHONPATH="$PWD/software/solarcare" python3 -m pytest -q software/tests/
```

En el entorno de desarrollo se utilizó un ejecutable del entorno virtual:

```bash
PYTHONPATH="$PWD/software/solarcare" \
  ~/Ollama_proy/.venv/bin/python -m pytest -q software/tests/
```

Para registrar una nueva ejecución reproducible también conviene anotar las versiones de Python/pytest y el commit probado:

```bash
git rev-parse --short HEAD
python3 --version
python3 -m pytest --version
```

El comando de versiones puede necesitar ejecutarse con el **mismo intérprete del entorno virtual** si Python/pytest no están instalados globalmente.

### 3.2. Resultado registrado

| Archivo de pruebas | Casos individuales generados | Resultado de la ejecución local |
| --- | ---: | --- |
| [`test_detector_solarcare.py`](../software/tests/test_detector_solarcare.py) | 12 | Aprobados |
| [`test_detector_transitorios.py`](../software/tests/test_detector_transitorios.py) | 9 | Aprobados: 6 sintéticos y 3 parametrizados con CSV históricos disponibles |
| [`test_ausencia_datos.py`](../software/tests/test_ausencia_datos.py) | 7 | Aprobados |
| [`test_cambio_dia_solarcare.py`](../software/tests/test_cambio_dia_solarcare.py) | 1 | Aprobado |
| [`test_integracion.py`](../software/tests/test_integracion.py) | 10 | Aprobados con simuladores del agente cuando corresponde |
| **Total** | **39** | **`39 passed` en Ubuntu, con los CSV históricos locales** |

El conteo de casos en `test_detector_transitorios.py` distingue las **tres instancias** de `@pytest.mark.parametrize` de una sola definición de función: 6 pruebas sintéticas + 3 pruebas históricas = **9 casos**.

**Condición de reproducibilidad:** los tres casos históricos buscan archivos bajo `software/tests/datos_historicos/Registro inversor 2(1)/Registro inversor 2/`. Esa carpeta de datos **no se sube a Git**. Si los CSV no existen localmente, pytest ejecuta `pytest.skip(...)` en esos tres casos. Por ello, en un clon limpio se espera que pasen **36 casos y se omitan 3**, siempre que el entorno y el código no hayan cambiado. Las omisiones **no deben contarse como aprobaciones**.

La ejecución original sin esos archivos produjo `36 passed, 3 failed` por `FileNotFoundError`; después se corrigió la prueba para omitir los casos que necesitan archivos no disponibles y, utilizando un enlace local hacia los históricos autorizados, se comprobó `39 passed`. Este incidente fue un **problema de localización de datos de prueba**, no evidencia de que hubiera fallado el algoritmo de detección.

### 3.3. Pruebas del detector: 12 casos

| Caso | Función de prueba | Comportamiento verificado |
| --- | --- | --- |
| D-01 | `test_sin_anomalias_constantes` | Potencia y corrientes constantes no producen eventos. |
| D-02 | `test_cero_fuera_de_horario_no_genera_interrupcion` | Potencia cero fuera de horario no genera interrupción de prueba. |
| D-03 | `test_interrupcion_sostenida_con_generacion_previa` | Caída prolongada tras generación suficiente produce una interrupción. |
| D-04 | `test_interrupcion_breve_no_genera_alarma` | Una caída breve sin confirmación no se trata como interrupción sostenida. |
| D-05 | `test_caida_aislada_sostenida_corriente_cc` | Descenso aislado prolongado de una entrada CC genera evento. |
| D-06 | `test_caida_conjunta_no_es_caida_aislada` | Descenso simultáneo de varias entradas no se presenta como caída aislada. |
| D-07 | `test_hueco_no_confirma_caida_de_corriente` | Un hueco de adquisición evita confirmar caída sostenida de corriente. |
| D-08 | `test_hueco_no_confirma_interrupcion` | Un hueco de adquisición evita confirmar interrupción sostenida. |
| D-09 | `test_intervalos_sin_huecos` | Calcula correctamente intervalo mediano y ausencia de huecos relevantes. |
| D-10 | `test_csv_incompleto_falla_con_mensaje` | Rechaza CSV sin columnas eléctricas obligatorias. |
| D-11 | `test_csv_valores_incorrectos_rechazados` | Rechaza valores no finitos como `NaN`. |
| D-12 | `test_dos_eventos_separados_se_detectan` | Reconoce dos episodios diferenciados por recuperación intermedia. |

**Cobertura funcional principal:** RF-05, RF-09, RF-10 y RF-11. Ninguno de estos casos cuantifica por sí mismo sensibilidad, precisión global o tasa de falsos positivos en un conjunto independiente de datos reales.

### 3.4. Transitorios: 9 casos

Las pruebas sintéticas verifican detección con generación previa/posterior, tensiones CC presentes, límites temporales, recuperación y horario. No se confirma un evento transitorio si faltan tensiones, se observan huecos amplios, no hay recuperación, se está fuera del horario o se presentan dos mediciones centrales en cero que no cumplen el patrón de una única muestra.

Además, se parametrizan tres CSV históricos con fechas de eventos documentados en el propio código de prueba:

| CSV histórico (local, no publicado) | Marcas temporales esperadas |
| --- | --- |
| `Marzo 2026/2026-03-11.csv` | 2026-03-11 09:08:21 |
| `Mayo 2026/2026-05-13.csv` | 2026-05-13 10:46:09 |
| `Junio 2026/2026-06-07.csv` | 2026-06-07 12:50:42, 13:02:58 y 13:48:56 |

La prueba exige que esas marcas se encuentren dentro del conjunto de eventos transitorios obtenidos. **No demuestra automáticamente** que exista una causa física confirmada en esos instantes; es una verificación del comportamiento del algoritmo contra casos previamente identificados.

Para un transitorio, `duracion_maxima_minutos` representa la **cota superior temporal entre muestras con generación**, no la duración exacta de una desconexión.

### 3.5. Ausencia y recuperación de datos: 7 casos

| Caso | Función de prueba | Comportamiento verificado |
| --- | --- | --- |
| A-01 | `test_datos_actualizados` | Dato reciente dentro del umbral ⇒ `actualizado`. |
| A-02 | `test_ausencia_de_datos` | Dato con antigüedad superior al umbral ⇒ `sin_actualizacion`. |
| A-03 | `test_fuera_de_horario` | No genera una evaluación ordinaria de frescura fuera de la ventana prevista. |
| A-04 | `test_archivo_no_disponible` | Distingue ausencia del archivo esperado. |
| A-05 | `test_archivo_sin_mediciones` | Identifica CSV sin fechas válidas. |
| A-06 | `test_fecha_futura_incorrecta` | Rechaza una marca temporal futura fuera de tolerancia. |
| A-07 | `test_recuperacion_de_datos` | Reconoce actualización al incorporar una nueva marca temporal tras ausencia. |

**Alcance:** se prueban estados de `verificar_actualizacion()` mediante tiempo simulado. Esto no significa que se haya medido el retraso real de la máquina virtual ni que se haya probado el servicio web del SESLAB (RF-06/RF-07).

### 3.6. Cambio automático de día: 1 caso

[`test_cambio_automatico_de_dia`](../software/tests/test_cambio_dia_solarcare.py) emplea un reloj simulado y reemplaza la inspección y el sueño del monitor con funciones controladas. Comprueba que se consulta el archivo de un día y, al cambiar la fecha, el archivo del día siguiente.

Esta prueba demuestra **la lógica de selección de ruta**, no una observación de dos jornadas reales de operación continua en Raspberry Pi.

### 3.7. Publicación, cola y fallos de IA: 10 casos

[`test_integracion.py`](../software/tests/test_integracion.py) se ejecuta **sin Ollama real** mediante un analizador simulado cuando se necesita controlar resultados. Los casos incluyen:

| Caso | Función de prueba | Comportamiento verificado |
| --- | --- | --- |
| I-01 | `test_alerta_se_guarda_antes_de_ia` | La alerta existe en CSV antes de cualquier inferencia. |
| I-02 | `test_no_modifica_csv_original_de_muestra` | Publicar una alerta no modifica un archivo sintético de muestra. |
| I-03 | `test_ia_completa_guarda_resultado_y_libera_cola` | Un estado `completo` se guarda y retira el evento de la cola. |
| I-04 | `test_fallo_de_ia_deja_alerta_y_pendiente` | Se conserva la alerta y el evento si IA no está disponible. |
| I-05 | `test_pendiente_se_reintenta_cuando_ia_vuelve` | El evento pendiente puede procesarse después sin duplicar la alerta previa. |
| I-06 | `test_interpretacion_parcial_se_conserva_para_reintentar` | Un resultado `parcial` se mantiene en cola. |
| I-07 | `test_evento_invalido_se_aparta_de_la_cola` | Un estado inválido se mueve al directorio de eventos inválidos. |
| I-08 | `test_excepcion_del_agente_no_borra_evento` | Una excepción del analizador no elimina el evento. |
| I-09 | `test_multiples_eventos_tienen_ids_distintos` | Publicaciones directas reciben identificadores distintos. |
| I-10 | `test_encolar_sin_duplicar_csv_del_detector` | Es posible encolar sin crear un segundo registro de alerta. |

**Precisiones:** I-09 utiliza `publicar_evento()`, no el mecanismo de deduplicación de `publicar_evento_unico()`; no debe describirse como prueba de que se evita automáticamente duplicar todo evento. I-02 verifica una **fuente sintética** durante publicación; no sustituye los hashes SHA-256 exigidos para validar la integridad de archivos SESLAB reales.

El evento fijo usado por estas pruebas es un **objeto sintético** que sirve para verificar almacenamiento y manejo de estados. No es una medición de campo y no valida los umbrales eléctricos del detector.

## 4. Pruebas manuales con los modelos Tev1 y Qwen3

Durante el desarrollo local en Ubuntu se realizaron pruebas de interpretación real de eventos. Se verificó que:

- El agente puede consultar `tev1:0.8b` y obtener una puntuación numérica de revisión.
- Qwen3 puede emitir una explicación, hipótesis y recomendación para el evento seleccionado.
- Un evento transitorio puede describirse con sus potencias anterior, durante y posterior, corrientes y tensiones medidas, y la duración expresada como cota superior.
- El chat Flask puede mantener contexto conversacional y responder a preguntas sobre el evento.

Para completar su **evidencia académica reproducible**, debe incorporarse una ficha de prueba con la versión exacta de cada modelo, entrada de ejemplo **autorizada o sintética**, salida estructurada, duración medida y evaluación técnica de los resultados.

**RF-15 continúa parcial:** una puntuación numérica Tev1 no equivale todavía a la categoría y prioridad explícitas exigidas en el diseño. **RF-16 tiene funcionamiento local demostrado**, sujeto a completar evidencias y prueba embebida.

## 5. Pruebas manuales de la interfaz Flask

La versión 2 del dashboard se abrió y utilizó en Ubuntu. Se observaron indicadores, gráfica, selección de anomalías, interpretación y chat. Se utilizaron archivos de prueba y resultados previos.

| ID | Verificación propuesta para documentar formalmente | Criterio esperado | Evidencia disponible |
| --- | --- | --- | --- |
| F-01 | Abrir `GET /` | Se muestra la interfaz sin error HTTP | Observación local; captura pendiente de archivar |
| F-02 | Consultar `GET /api/estado` | Se devuelven mediciones/alertas coherentes con CSV configurado | Código implementado y observación local; falta prueba HTTP automatizada |
| F-03 | Cambiar fecha | Se actualiza el período sin mezclar alertas de otros días | Implementado; caso de aceptación pendiente |
| F-04 | Seleccionar una anomalía | Muestra evidencia y resultado IA correspondiente al mismo ID | Implementado y observado localmente; captura formal pendiente |
| F-05 | Preguntar a Qwen3 | Respuesta contextual o error explícito si no está disponible | Observado localmente; log de prueba pendiente |
| F-06 | Cargar CSV inexistente o inválido | Aviso de indisponibilidad, sin interpretar ausencia como generación normal | Código preparado; prueba de aceptación pendiente |
| F-07 | Usar DEMO | Valores identificados como ilustrativos, no reales | Código preparado; captura formal pendiente |
| F-08 | Acceder desde navegador externo a Raspberry Pi | Interfaz disponible por red autorizada y protegida | **No verificado** |

**Advertencia:** la actualización del navegador cada 25 segundos no demuestra datos en tiempo real estricto. La frescura de los CSV requiere verificación separada.

## 6. Verificación de conectividad y actualización de la máquina virtual

El equipo reportó que **ya logró conectarse a la máquina virtual del SESLAB y consultar CSV que se actualizan con retraso**. Este avance es una evidencia de acceso a la fuente, pero no se debe afirmar, hasta completar el registro, que la prueba ocurrió necesariamente **desde Raspberry Pi** o que se procesó automáticamente toda la cadena.

### 6.1. Ficha de medición de retraso para completar

| Observación | Hora de la medición en el CSV | Hora en que se hizo visible | Retraso calculado | Equipo desde el que se consultó |
| --- | --- | --- | --- | --- |
| Muestra 1 | Por registrar | Por registrar | Por calcular | Por registrar |
| Muestra 2 | Por registrar | Por registrar | Por calcular | Por registrar |
| Muestra 3 | Por registrar | Por registrar | Por calcular | Por registrar |

El retraso debe estimarse comparando marcas temporales sobre una base horaria coherente. No convertir una observación puntual en una latencia media o máxima del sistema.

**Pendiente:** documentar protocolo autorizado, características del acceso solo lectura, condiciones de la red y manejo de una interrupción de comunicación. No publicar IP privadas, nombres de cuenta ni contraseñas.

## 7. Plan de aceptación en Raspberry Pi con Yocto

Los casos siguientes se plantean **para ser ejecutados y documentados por el equipo** cuando la integración esté lista. Su estado es **pendiente de validación**, salvo que se agregue posteriormente evidencia real.

| ID | Objetivo | Evidencia mínima | Estado |
| --- | --- | --- | --- |
| Y-01 | Reconocer `meta-solarcare` en BitBake | Versión de Yocto, `MACHINE`, capas reconocidas | Pendiente |
| Y-02 | Compilar `solarcare-image` | Resumen BitBake, artefacto generado y hash | Pendiente |
| Y-03 | Arrancar Raspberry Pi con la imagen | Log/identificación del sistema, kernel, fecha | Pendiente |
| Y-04 | Iniciar Ollama local | Estado de servicio y respuesta desde loopback | Pendiente |
| Y-05 | Inferir con Tev1 y Qwen3 | Versiones, respuestas, RAM, CPU y tiempo | Pendiente |
| Y-06 | Leer CSV remoto autorizado | Prueba de acceso de solo lectura y marcas temporales de datos | Pendiente |
| Y-07 | Publicar anomalía eléctrica | Archivo de alerta y evidencia de detección | Pendiente |
| Y-08 | Procesar cola y guardar JSON | Relación `id_evento` entre alerta y resultado | Pendiente |
| Y-09 | Recuperarse de Ollama no disponible | Detector independiente, evento pendiente, reintento | Pendiente |
| Y-10 | Mostrar dashboard desde navegador autorizado | Servidor web, ruta, mediciones y estado de IA | Pendiente |
| Y-11 | Persistir resultados tras reinicio | Comparación de archivos/servicios antes y después | Pendiente |
| Y-12 | Medir desempeño y uso de recursos | Tabla con CPU, RAM, espacio, tiempos y condiciones | Pendiente |

La descripción de servicios y comandos de observación está en [07_integracion_yocto.md](07_integracion_yocto.md). Ninguna de las doce pruebas se considera aprobada únicamente por la presencia de recetas o unidades `systemd` en Git.

## 8. Pruebas faltantes para cerrar requisitos específicos

| Requisito | Brecha | Prueba de aceptación recomendada |
| --- | --- | --- |
| RF-03 | No existe registro persistente por fila procesada | Añadir filas a un CSV en ejecución y comprobar procesamientos incrementales con criterio definido. |
| RF-06/RF-07 | No hay verificación HTTP de la aplicación web original | Simular caída controlada del servicio **sin intervenir la generación**; demostrar datos actualizados y evento de indisponibilidad web. |
| RF-15 | Tev1 no retorna categoría y prioridad explícitas | Definir el contrato requerido y verificar esquema/valores de salida. |
| RNF-01 | Solo lectura no verificada mediante hashes en la fuente final | Calcular SHA-256 antes y después de una lectura autorizada y confirmar coincidencia. |
| RNF-04 | Errores de lectura no tienen log persistente formal | Inyectar CSV corrupto y comprobar archivo/journal de errores recuperable. |
| RNF-05 | Umbrales están en constantes del detector | Cambiar parámetro externo y verificar efecto sin editar el código Python. |
| RNF-06 | Independencia comprobada con simulador | Detener solo Ollama y verificar alerta/cola reales en Raspberry Pi. |
| RNF-07 | Falta inferencia embebida sin Internet | Desconectar salida a Internet manteniendo red local autorizada y comprobar ambas inferencias. |
| RNF-08 | Faltan métricas del hardware objetivo | Medir memoria, CPU y latencia de Tev1, Qwen3 y detector en operación simultánea. |

No deben realizarse pruebas que impliquen manipular, apagar o desconectar equipos eléctricos energizados sin autorización y personal capacitado. Para verificar caídas de servicios pueden usarse entornos simulados o servicios de prueba aislados.

## 9. Criterios generales para declarar una prueba aprobada

Una prueba solo deberá declararse **«Aprobada»** cuando exista correspondencia entre:

1. **Caso y requisito:** identificadores y versión del criterio utilizado.
2. **Entorno:** sistema operativo, equipo, versión de software e infraestructura.
3. **Condiciones iniciales:** servicios activos, datos sintéticos/autorizados y hora coherente.
4. **Procedimiento:** comandos o acciones que permitan repetirla.
5. **Resultado esperado:** regla de aceptación definida antes de ejecutar.
6. **Resultado observado:** salida, archivo o métrica real con fecha.
7. **Evidencia:** captura, log anonimizado o reporte vinculado desde Git.
8. **Conclusión:** Aprobada, Fallida, Bloqueada o No ejecutada; justificación de desviaciones.

Se preparó una [plantilla reutilizable de evidencia](evidencias/plantilla_registro_prueba.md) para aplicar este criterio a las pruebas finales.

## 10. Registro de resultados y limitaciones

**Resultados disponibles a la fecha:**

- **39 pruebas automatizadas aprobadas en Ubuntu** con datos históricos locales, incluyendo 3 casos dependientes de CSV no distribuidos.
- Funcionamiento manual del detector, agente Tev1/Qwen3 y dashboard con chat en Ubuntu.
- Conectividad con la VM y visualización de datos recientes **reportadas por el equipo**, todavía sin protocolo ni métricas de retraso anexados.
- Recetas y servicios de Yocto publicados; ejecución integral en Raspberry Pi **sin evidencia de aceptación incorporada**.

**Límites de inferencia:** estas comprobaciones no aportan una tasa medida de falsos positivos, un diagnóstico físico confirmado, seguridad de producción, integridad criptográfica de todos los CSV ni compatibilidad definitiva con el hardware objetivo.

### 10.1. Evidencias aún por recopilar

Para cerrar la documentación final se necesita:

- Registro de ejecución de `pytest` con fecha, intérprete, commit y resultado.
- Capturas autorizadas de detector, alertas y archivo de cola.
- Evidencia anonimizada de entrada/salida Tev1 y Qwen3, con tiempos medidos.
- Capturas del dashboard, incluida la indicación de datos locales/no en vivo.
- Registro de la conexión a la VM, latencias de publicación CSV y verificación de solo lectura.
- Logs de BitBake, arranque, servicios `systemd` y mediciones de recursos de Raspberry Pi.

**Política de datos:** en GitHub almacenar solo resultados y capturas que no revelen contraseñas, IP privadas, credenciales, archivos institucionales restringidos o información de acceso sensible. Los CSV originales del SESLAB **no forman parte del repositorio**.

---

**Documentos relacionados:** [Matriz de requerimientos](02_matriz_requerimientos.md) · [Arquitectura](03_arquitectura_del_sistema.md) · [Detector](04_implementacion_del_detector.md) · [IA](05_integracion_inteligencia_artificial.md) · [Interfaz](06_interfaz_grafica.md) · [Yocto](07_integracion_yocto.md) · [Índice](README.md).
