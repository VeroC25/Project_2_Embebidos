# Implementación del detector y monitoreo de anomalías — SolarCare AI

> **Alcance:** implementación Python publicada en la rama `feature/solarcare-python-dashboard`, contrastada con la propuesta original de diseño.  
> **Estado:** funcional y probado localmente en Ubuntu; la ejecución integrada sobre Raspberry Pi con Yocto requiere evidencia adicional.  
> **Objeto de supervisión:** registros del inversor 2 del SESLAB. Las cuatro entradas CC se denominan **entradas** y no se presupone que correspondan a cuatro MPPT independientes.

## 1. Objetivo y principio de operación

El componente detector procesa registros eléctricos CSV del sistema de monitoreo **existente** del SESLAB, identifica patrones que justifican revisión técnica y los registra sin alterar los archivos fuente. No utiliza IA para decidir si hay una anomalía: los eventos se generan mediante **reglas deterministas** implementadas en Python. La interpretación con Tev1 y Qwen3 constituye un procesamiento posterior e independiente.

La solución implementa tres familias de eventos operativos:

1. **Interrupción de generación**: sostenida o transitoria, según las muestras y el criterio de confirmación.
2. **Reducción sostenida de corriente continua** en una entrada, frente a una referencia histórica reciente y con corroboración de otras entradas.
3. **Ausencia de nuevas mediciones**: desactualización de un CSV dentro de una ventana horaria de supervisión.

La **indisponibilidad de la aplicación web del SESLAB cuando los datos continúan actualizándose** es una cuarta categoría especificada en la propuesta original, pero **todavía no se identificó implementada** como verificación HTTP y correlación automática (RF-06 y RF-07).

Los módulos principales son:

| Archivo | Función |
| --- | --- |
| [`detector_solarcare.py`](../software/solarcare/detector_solarcare.py) | Lectura, validación y detección de anomalías eléctricas. |
| [`monitorear_csv_solarcare.py`](../software/solarcare/monitorear_csv_solarcare.py) | Inspección y seguimiento opcional de cambios en un CSV. |
| [`monitor_diario_solarcare.py`](../software/solarcare/monitor_diario_solarcare.py) | Selección del archivo diario, supervisión periódica, invocación del detector y estados. |
| [`detectar_ausencia_datos.py`](../software/solarcare/detectar_ausencia_datos.py) | Evaluación de la antigüedad de la última medición. |
| [`eventos_ausencia_solarcare.py`](../software/solarcare/eventos_ausencia_solarcare.py) | Construcción de un evento de ausencia de datos. |
| [`seguimiento_estado_datos.py`](../software/solarcare/seguimiento_estado_datos.py) | Persistencia del estado y reconocimiento de recuperación de datos. |
| [`publicacion_unica.py`](../software/solarcare/publicacion_unica.py) | Evita duplicar alertas de un mismo evento. |
| [`puente_detector_ia.py`](../software/solarcare/puente_detector_ia.py) | Registra alertas en un CSV independiente y publica JSON para IA. |

## 2. Modelo de datos y validación de entrada

La función `leer_csv(ruta)` abre el archivo con `Path.open("r", encoding="utf-8-sig", newline="")` y `csv.DictReader`. Los campos **obligatorios** son:

| Columna original | Interpretación |
| --- | --- |
| `Last update time` | Fecha y hora de la medición. |
| `AC output power(W)` | Potencia de salida de CA, en watts. |
| `DC current 1(A)` | Corriente de entrada CC 1, en amperios. |
| `DC current 2(A)` | Corriente de entrada CC 2, en amperios. |
| `DC current 3(A)` | Corriente de entrada CC 3, en amperios. |
| `DC current 4(A)` | Corriente de entrada CC 4, en amperios. |

Si están presentes las tensiones `DC voltage 1(V)` a `DC voltage 4(V)`, se exigen **las cuatro columnas** para incorporarlas al análisis; si no está ninguna, la detección sostenida aún puede trabajar, pero no se confirmarán transitorios que requieren tensión CC.

La lectura valida:

- Encabezados obligatorios y existencia de datos.
- Formato de fecha y hora `YYYY-MM-DD HH:MM:SS`.
- Conversión numérica de potencia, corrientes y tensiones opcionales.
- Valores no negativos y finitos (`NaN` e infinito no son aceptados).
- Marcas temporales estrictamente crecientes.

Una fila inválida puede producir `ValueError` con referencia a su línea; el monitor informa el problema y reintenta en una iteración posterior, si está en modo continuo. El comportamiento publicado **no equivale** todavía a un mecanismo completo de almacenamiento persistente de errores (RNF-04).

La estructura interna `Medicion` conserva `instante`, `potencia_w`, cuatro `corrientes_a` y, cuando existen, cuatro `tensiones_v`. La lectura **no escribe** sobre el CSV original; queda por adjuntar una prueba formal de hashes SHA-256 en la infraestructura final (RNF-01).

## 3. Parámetros implementados: valores iniciales, no límites universales

Los valores siguientes se encuentran **definidos como constantes** en [`detector_solarcare.py`](../software/solarcare/detector_solarcare.py). Son parámetros iniciales de las pruebas y **no deben presentarse como umbrales certificados o calibrados para cualquier condición fotovoltaica**.

| Constante | Valor actual | Uso |
| --- | ---: | --- |
| `HORA_INICIO` / `HORA_FIN` | 08:00–15:30 | Ventana provisional de generación esperada para detección eléctrica. |
| `DURACION_MINIMA_MIN` | 5 min | Confirmación de eventos sostenidos. |
| `POTENCIA_PREVIA_MIN_W` | 2000 W | Generación inmediatamente previa requerida para iniciar una posible interrupción. |
| `POTENCIA_BAJA_W` | 100 W | Límite de potencia baja. |
| `POTENCIA_TRANSITORIA_MIN_W` | 3000 W | Potencia mínima de las muestras previa y posterior a un transitorio. |
| `TENSION_TRANSITORIA_MIN_V` | 400 V | Tensión mínima por entrada CC al observar el transitorio. |
| `CORRIENTE_TRANSITORIA_MAX_A` | 0,1 A | Corriente máxima por entrada CC en la muestra anómala transitoria. |
| `CORRIENTE_REFERENCIA_MIN_A` | 2,0 A | Corriente de referencia mínima para evaluar una entrada. |
| `CAIDA_CORRIENTE_MIN_FRACCION` | 0,50 | Caída de corriente mínima del 50 %. |
| `PARES_ESTABLES_MIN` | 2 | Número mínimo de otras entradas que deben permanecer relativamente estables. |
| `CAMBIO_MAX_OTRAS_FRACCION` | 0,25 | Reducción tolerada del 25 % frente a la referencia de las otras entradas. |
| `VENTANA_REFERENCIA` | 5 muestras | Tamaño de la ventana para calcular medianas de corriente. |
| `HUECO_MAX_SEGUNDOS` | 300 s | Separación máxima admitida entre muestras para mantener la evidencia de continuidad. |

**Limitación relevante — RNF-05:** estos umbrales no están expuestos todavía mediante un archivo de configuración o argumentos del detector; modificar sus valores exige editar código. Se deberá incorporar configuración externa si se pretende cumplir literalmente RNF-05.

## 4. Algoritmo de interrupción sostenida de generación

Se considera una **posible interrupción sostenida** únicamente cuando:

1. La medición está dentro de la ventana provisional de generación esperada.
2. La muestra anterior registra al menos **2000 W** de potencia.
3. La potencia cae a **100 W o menos**.
4. La condición de potencia baja permanece durante al menos **5 minutos desde la primera muestra baja**.
5. No aparece un hueco de más de **300 segundos** que invalide la continuidad de la evidencia.

Al confirmarse, se emite `evento="interrupcion_generacion"` con potencia previa, potencia actual, fecha de inicio y tiempo **hasta la confirmación**. El campo `duracion_tipo="hasta_confirmacion"` evita interpretar esa cifra como duración final de la falla.

La condición no se confirma si la potencia se recupera antes de la duración mínima o si ocurre fuera del horario evaluado. Una vez reportado, el episodio no vuelve a emitirse por cada nueva muestra baja durante la misma ejecución.

**Decisión técnica:** exigir generación previa y continuidad disminuye alertas por períodos normales de baja producción y por intervalos en los que faltan mediciones. No asegura que se haya producido una falla física del inversor: se necesita revisión técnica.

## 5. Algoritmo de interrupción transitoria

La función `detectar_transitorios(mediciones)` analiza **tres mediciones consecutivas del mismo día**:

```text
Muestra anterior              Muestra anómala               Muestra posterior
Potencia > 3000 W      ->     Potencia <= 100 W      ->     Potencia > 3000 W
                                CC <= 0,1 A
                                CC > 400 V
```

El código exige que las cuatro corrientes medidas en la muestra central no superen **0,1 A**, que estén disponibles las cuatro tensiones y que cada una sea **mayor que 400 V**. Ambas separaciones temporales deben ser mayores que cero y **no superar 300 segundos**. También se exige el horario de prueba.

El evento se registra como `interrupcion_generacion`, con `subtipo="transitoria"` y `recuperacion_observada`.

La duración física exacta del evento **no puede determinarse a partir de tres lecturas discretas**. Por ello, se calcula una *cota superior observacional* con la distancia temporal entre la última muestra con generación previa y la primera muestra que demuestra recuperación:

```text
duracion_maxima_minutos =
    (tiempo_muestra_posterior - tiempo_muestra_anterior) / 60
```

Por ejemplo, una ventana de **3,07 minutos** entre dos muestras con generación alrededor de una muestra en cero **no significa** que el inversor estuvo detenido exactamente 3,07 minutos.

La implementación evita confirmar este subtipo si faltan tensiones, no existe recuperación observada, hay huecos amplios o el evento queda fuera de horario.

## 6. Algoritmo de reducción sostenida de corriente CC

Para cada una de las **cuatro entradas CC** se calcula una **referencia propia** a partir de la mediana de las **cinco mediciones anteriores**. La referencia se congela al iniciar un posible evento; esto impide que la propia caída reduzca inmediatamente el valor de referencia utilizado para confirmar el episodio.

Para la entrada `i`:

```text
referencia_i = mediana(I_i en las 5 muestras previas)

reduccion_i(%) = 100 * (1 - corriente_actual_i / referencia_i)
```

Se inicia un candidato si:

- `referencia_i >= 2,0 A`.
- `corriente_actual_i <= 0,5 * referencia_i` (reducción de **50 % o más**).
- La medición ocurre dentro del horario establecido.

Para mantener y confirmar el candidato:

- Debe observarse la condición durante al menos **5 minutos**.
- **Al menos dos de las otras tres entradas** deben mantener una corriente igual o superior al **75 %** de su propia referencia congelada, y esa referencia debe ser al menos 2,0 A.
- No deben existir huecos superiores a 300 s que rompan la continuidad.

El resultado `reduccion_corriente_dc` incluye `entrada_cc`, `corriente_referencia_a`, `corriente_medida_a`, `reduccion_porcentual`, tiempo hasta confirmación y marcas temporales.

**Justificación:** no se comparan directamente corrientes absolutas de entradas potencialmente distintas; cada una tiene su propio historial reciente. La estabilidad relativa de otras entradas actúa como corroboración para reducir alertas ante disminuciones generales. No sustituye conocer el cableado, configuración de MPPT ni irradiancia real.

## 7. Ausencia de datos y recuperación: función distinta del detector eléctrico

La supervisión de disponibilidad se implementa mediante [`verificar_actualizacion()`](../software/solarcare/detectar_ausencia_datos.py). A diferencia de los algoritmos eléctricos, **no analiza la generación como evidencia de falla física**. Compara la hora actual con la marca temporal **más reciente** del CSV.

Valores actuales:

| Parámetro | Valor | Consideración |
| --- | --- | --- |
| Ventana horaria de supervisión de datos | **07:00–18:00** | Provisional e independiente de la ventana eléctrica 08:00–15:30. |
| Umbral de antigüedad | **20 minutos** | Se declara `sin_actualizacion` si el retraso **supera** 20 minutos. |
| Tolerancia a fechas futuras | **2 minutos** | Registra `fecha_inconsistente` si la marca temporal supera ese margen. |

Estados internos posibles:

- `fuera_de_horario`: no se evalúa la frescura fuera de la ventana.
- `archivo_no_disponible`: no existe el archivo esperado.
- `sin_mediciones`: no hay fechas válidas.
- `fecha_inconsistente`: existen marcas temporales futuras fuera de tolerancia.
- `actualizado`: la medición más reciente está dentro del umbral.
- `sin_actualizacion`: la medición más reciente excede el umbral de antigüedad.

**Importante:** en el monitor publicado, la creación y publicación de `ausencia_datos` se dispara específicamente para el estado **`sin_actualizacion`**, si se activan `--verificar-datos` y `--publicar-estados`. `archivo_no_disponible` y `sin_mediciones` se informan como estados, pero no se convierten automáticamente en el mismo tipo de alerta.

`seguimiento_estado_datos.py` almacena `ausencia_activa` y `ultima_medicion` en un archivo JSON de estado mediante reemplazo atómico. Cuando el sistema pasa de una ausencia activa a un estado actualizado **y la marca temporal avanza**, devuelve una notificación `recuperacion_datos` que el monitor **imprime**. En la integración publicada no se identificó que esa recuperación se persista como una alerta normal en `alertas_anomalias.csv`.

El equipo reportó haber accedido a CSV recientes de la máquina virtual y observado retraso entre la medición y su disponibilidad. **La magnitud y variabilidad de ese retraso requieren medición documentada**: el umbral provisional de 20 minutos no está validado todavía contra la distribución real de latencias del SESLAB.

## 8. Supervisión automática y diferencia entre refrescar y procesar

[`monitor_diario_solarcare.py`](../software/solarcare/monitor_diario_solarcare.py) localiza el archivo del día con la ruta relativa:

```text
<raiz>/<YYYY-MM-DD>/<YYYY-MM-DD>.csv
```

En modo `--continuo`:

1. Determina la fecha actual y el CSV esperado.
2. Detecta un cambio de fecha para consultar automáticamente el CSV del nuevo día.
3. Comprueba si cambió el par `(mtime_ns, tamaño)`.
4. Si existe una versión nueva, vuelve a leer y analizar el CSV.
5. Con `--verificar-datos`, también comprueba la frescura del archivo incluso si no cambió.
6. Si están habilitadas las opciones de publicación, registra eventos y estados cuando corresponda.
7. Duerme el número configurado de segundos y repite.

El intervalo predeterminado es de **10 segundos** para el ciclo de consulta; **no significa** que los instrumentos de campo generen nuevas mediciones cada 10 segundos ni que la latencia de la VM sea de 10 segundos.

**Alcance real de RF-03:** actualmente se usa una estrategia de *reinspección por versión del CSV* y *deduplicación por evento*. No existe todavía un índice persistente por fila que pruebe exactamente qué registros de medición se han procesado.

### 8.1. Ejemplo de ejecución local sin publicar alertas

Desde la raíz del repositorio y con Python preparado:

```bash
PYTHONPATH="$PWD/software/solarcare" python3   software/solarcare/detector_solarcare.py   /ruta/a/archivo_de_prueba.csv
```

La ejecución anterior **solo inspecciona** el CSV. Para analizar automáticamente la estructura de carpetas diarias sin publicar alertas:

```bash
PYTHONPATH="$PWD/software/solarcare" python3   software/solarcare/monitor_diario_solarcare.py   --raiz /ruta/autorizada/Inversor\ 2   --continuo --intervalo 10 --verificar-datos
```

Las rutas son ejemplos; el acceso remoto y los permisos deben definirse con el personal autorizado. Se debe evitar publicar datos reales de uso restringido en GitHub.

### 8.2. Publicación de alertas

Para el análisis de un archivo, `--publicar` habilita la llamada a `publicar_evento_unico()`. En el monitor diario, `--publicar-electricas` habilita alertas eléctricas; `--publicar-estados` habilita publicación de `sin_actualizacion` y exige `--verificar-datos`.

El monitor dispone de `--salidas` para los estados y eventos de ausencia. **Detalle de integración:** las alertas eléctricas llamadas desde `inspeccionar()` usan actualmente el directorio de salidas por defecto del módulo publicador, mientras que `--salidas` se usa explícitamente para ausencia y seguimiento. Debe verificarse que ambas rutas **apunten realmente al mismo almacenamiento** en Ubuntu y Yocto. La rama de integración Yocto prepara un enlace hacia `/var/lib/solarcare/salidas` desde la carpeta instalada en `/opt/solarcare`, pero requiere prueba en dispositivo.

## 9. Alertas, evidencia y prevención de duplicados

La detección puede devolver una lista de **eventos candidatos**. La publicación es opcional y se mantiene separada del cálculo. Cuando se habilita:

1. Se utiliza una clave lógica: `(inversor, evento, subtipo, entrada_cc, inicio_evento)`.
2. Se consulta `alertas_anomalias.csv` para detectar registros equivalentes.
3. Si el evento es nuevo, se genera un ID único y se escribe una fila con metadatos y `evento_json`.
4. Posteriormente se crea un archivo en `cola_ia/` para que el trabajador solicite la interpretación de IA.
5. Si la cola falla, el CSV de alerta ya quedó registrado; la IA no bloquea el registro.

`publicacion_unica.py` usa un bloqueo del archivo de control mediante `fcntl.flock` para coordinar publicaciones concurrentes. La estructura de salida no altera el CSV fuente.

**Límite:** la identidad de los eventos depende de sus campos clave; si un evento cambia de fecha de inicio, puede considerarse diferente. La deduplicación de alertas tampoco es por sí misma una garantía de procesamiento incremental de todas las muestras.

## 10. Pruebas y resultados disponibles

Las pruebas automatizadas se ubican en [`software/tests/`](../software/tests/):

| Archivo de pruebas | Escenarios relevantes |
| --- | --- |
| [`test_detector_solarcare.py`](../software/tests/test_detector_solarcare.py) | Operación estable, interrupción sostenida o breve, caída aislada de corriente, caída conjunta, huecos temporales, CSV inválidos y episodios separados. |
| [`test_detector_transitorios.py`](../software/tests/test_detector_transitorios.py) | Evento transitorio, ausencia de tensiones, huecos, falta de recuperación, horario inválido y casos históricos del SESLAB cuando hay CSV disponibles localmente. |
| [`test_ausencia_datos.py`](../software/tests/test_ausencia_datos.py) | Frescura, datos desactualizados, fuera de horario, archivo ausente, CSV sin mediciones, fechas futuras y recuperación. |
| [`test_cambio_dia_solarcare.py`](../software/tests/test_cambio_dia_solarcare.py) | Selección del archivo diario tras el cambio de fecha, mediante reloj y funciones simuladas. |
| [`test_integracion.py`](../software/tests/test_integracion.py) | Registro previo a IA, preservación de entradas, cola y reintentos ante fallas, entre otros escenarios. |

En la ejecución realizada en Ubuntu el **11 de noviembre de 2026**, el conjunto registró **39 passed** con tres CSV históricos disponibles mediante enlace local. Sin esos archivos, tres pruebas específicas se marcan como **skipped**; se mantienen ejecutables las pruebas con datos sintéticos.

Comando desde la raíz del repositorio:

```bash
PYTHONPATH="$PWD/software/solarcare" python3 -m pytest -q software/tests/
```

**Alcance de la evidencia:** las pruebas automatizadas y los casos locales no sustituyen una prueba de extremo a extremo con los servicios, adquisición remota, Ollama y modelos reales sobre Raspberry Pi.

## 11. Correspondencia con requerimientos del diseño

| Requisito | Relación con este documento | Estado al momento de la revisión |
| --- | --- | --- |
| RF-02 | Supervisión periódica | Implementado en Ubuntu; acceso real automatizado por validar |
| RF-03 | Cambios de CSV y deduplicación de eventos | Parcial: falta trazabilidad incremental por registro |
| RF-04 | Análisis manual de CSV por argumento | Implementado localmente |
| RF-05 | Validación de encabezados y mediciones | Implementado localmente |
| RF-06 y RF-07 | Disponibilidad HTTP de la web del SESLAB | Pendiente |
| RF-08 | Ausencia de nuevas mediciones | Implementado localmente; umbral por calibrar |
| RF-09 | Interrupción de generación | Implementado localmente |
| RF-10 y RF-11 | Referencias y reducción sostenida de corriente CC | Implementado localmente |
| RF-12 a RF-14 | Eventos, terminal y CSV independiente | Implementado localmente |
| RNF-01 | Fuente de datos en modo lectura | Implementación de lectura; hashes por demostrar |
| RNF-02 y RNF-03 | Almacenamiento independiente y fechas originales | Implementación local |
| RNF-04 | Registro persistente de errores de lectura | Pendiente |
| RNF-05 | Umbrales sin editar código | Pendiente |
| RNF-06 | Alertas independientes de IA | Implementado y probado localmente |

La [matriz de trazabilidad completa](02_matriz_requerimientos.md) incluye la evaluación individual de todos los RF y RNF.

## 12. Límites y próximos pasos

**Pendientes técnicos antes de considerar validado el detector integrado:**

1. Documentar el método de acceso autorizado a la máquina virtual, verificando solo lectura y las marcas temporales de medición frente a disponibilidad.
2. Calibrar los horarios, umbrales y tiempos de confirmación con condiciones reales de operación, sin sobreinterpretar disminuciones debidas a irradiancia.
3. Implementar RF-06/RF-07: supervisión explícita de la aplicación web y correlación con CSV actualizados.
4. Exponer umbrales en configuración externa (RNF-05) y guardar errores de lectura de manera persistente (RNF-04).
5. Verificar rutas compartidas de resultados y persistencia tras reinicio en Raspberry Pi, así como permisos sobre la fuente.
6. Documentar pruebas de aceptación con fecha, versión del código, caso, entrada, resultado esperado y observado, y evidencia.
7. Confirmar el significado físico de las cuatro entradas CC; no tratarlas automáticamente como cuatro cadenas o cuatro MPPT diferentes.

**Conclusión técnica:** el detector constituye un módulo funcional, reproducible y desacoplado de la IA en Ubuntu. Su principal ventaja es exigir evidencia temporal y validaciones independientes de disponibilidad. Su despliegue embebido, calibración y comprobación con el flujo completo de datos SESLAB todavía requieren pruebas documentadas.

---

**Documentación relacionada:** [Arquitectura del sistema](03_arquitectura_del_sistema.md) · [Matriz de requerimientos](02_matriz_requerimientos.md) · [Índice técnico](README.md).
