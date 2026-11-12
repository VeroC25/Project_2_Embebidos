# SolarCare AI
## Contexto del proyecto, estado de implementación, pruebas y decisiones técnicas

**Proyecto:** Taller de Sistemas Embebidos — Instituto Tecnológico de Costa Rica (TEC)  
**Equipo:** Marycruz Fallas Barquero y Verónica Cambronero Solano  
**Plataforma:** Raspberry Pi 4 (8 GB RAM), Linux generado con Yocto Project  
**Fecha de actualización:** 12 de noviembre de 2026  
**Versión:** 2.0 — consolidación de la sesión de integración y pruebas  
**Alcance del documento:** registrar lo observado, los cambios realizados y los aspectos aún pendientes. No sustituye la guía reproducible de compilación de Yocto ni las bitácoras individuales.

---

## 1. Resumen ejecutivo

Durante la sesión del 12 de noviembre de 2026 se pasó de una imagen Yocto ya compilada y grabada en microSD, pero todavía pendiente de validación sobre el hardware, a un **prototipo funcional sobre la Raspberry Pi**. Se comprobó el arranque, la conectividad de red, el acceso de solo lectura a los CSV del SESLAB, la detección de un evento eléctrico real registrado en el inversor 2, la ejecución local de Ollama con los modelos `tev1:0.8b` y `qwen3:1.7b`, el procesamiento del agente de IA, el dashboard Flask y el chat técnico con Qwen3.

El sistema permitió consultar un evento del **12/11/2026 a las 09:29:20**, identificado como `ce2d59a7`, y obtener una interpretación automática. Se corrigieron dos problemas en la aplicación web y un problema de tiempo de espera del chat. **No se ha demostrado todavía que toda la configuración sobreviva un reinicio**, que el recurso SMB se monte automáticamente ni que la integración requerida de **JEV** esté implementada. La función de análisis manual de CSV históricos se **evaluó**, pero **no se implementó**.

**Estado general:** integración funcional demostrada durante la sesión; autonomía, reproducibilidad de la imagen y cobertura completa de requisitos aún pendientes de validación.

## 2. Objetivo y alcance de SolarCare AI

SolarCare AI complementa el monitoreo fotovoltaico existente en el SESLAB. Su caso inicial es el **inversor 2**. El detector de Python lee archivos CSV, comprueba su integridad y actualidad, detecta eventos y genera registros de alerta sin modificar los archivos originales. Un agente local de IA interpreta los eventos con dos modelos y una aplicación web presenta datos, gráficas, alertas y consultas en lenguaje natural.

El diseño separa tres responsabilidades:

1. **Detector independiente de la IA:** lectura de datos, reglas de detección, deduplicación y publicación de eventos.
2. **Agente de IA:** clasificación/priorización mediante Tev1 e interpretación técnica mediante Qwen3, ejecutados localmente con Ollama.
3. **Sistema embebido e integración:** Linux generado con Yocto, servicios systemd, red, almacenamiento y despliegue en Raspberry Pi.

Esta separación busca que un fallo de Ollama no detenga la adquisición y detección; **la independencia se planteó arquitectónicamente, pero falta una prueba de fallo controlado**.

## 3. Infraestructura y arquitectura comprobadas

### 3.1. Hardware y sistema operativo

- **Raspberry Pi:** modelo 4, 8 GB de RAM; Linux generado con Yocto, arrancado desde microSD.
- **Computadora anfitriona:** Ubuntu, utilizada para la conexión SSH y para compartir la conexión de red.
- **Aplicación web:** Flask, puerto TCP `8091`.
- **Motor de IA:** Ollama en la Raspberry Pi, API local `127.0.0.1:11434`.
- **Modelos presentes:** `tev1:0.8b` y `qwen3:1.7b`.
- **Python en Raspberry Pi:** versión observada `3.14.5`.

### 3.2. Red utilizada durante las pruebas

| Equipo / servicio | Dirección o recurso | Uso |
|---|---|---|
| Ubuntu anfitrión | `10.42.0.1` | Red Ethernet compartida con la Raspberry Pi |
| Raspberry Pi | `10.42.0.113` | SSH y dashboard |
| Máquina virtual / PC de monitoreo SESLAB | `<IP_SERVIDOR_SESLAB>` | Origen de archivos CSV |
| Compartición SMB | `//<IP_SERVIDOR_SESLAB>/<RECURSO_COMPARTIDO>` | Acceso a mediciones |
| Dashboard | `http://10.42.0.113:8091` | Interfaz de usuario |
| API local Ollama | `http://127.0.0.1:11434` | Inferencia local |

La topología usada fue **Ubuntu ↔ Ethernet ↔ Raspberry Pi**, con conectividad hacia la red del SESLAB a través de la configuración de red disponible durante la sesión. El funcionamiento de esta ruta no demuestra todavía operación completamente autónoma sin la computadora anfitriona.

### 3.3. Datos de entrada y política de acceso

La Raspberry Pi pudo acceder a la carpeta compartida de los inversores. Para el caso inicial se trabajó con:

```text
/var/lib/solarcare/datos/Inversor 2/2026-11-12/2026-11-12.csv
```

El recurso SMB se montó en `/var/lib/solarcare/datos` con acceso **de solo lectura** (`ro`), usando SMB 3.0 y el puerto 445. **El montaje se efectuó manualmente y no quedó demostrado como persistente después de reiniciar**. No se registran contraseñas en esta documentación.

## 4. Componentes de software y rutas

| Componente | Ruta / servicio | Estado observado |
|---|---|---|
| Monitor diario y detector | `/opt/solarcare/monitor_diario_solarcare.py` | Ejecutado y con evento detectado |
| Datos de origen | `/var/lib/solarcare/datos` | Compartición SMB accesible en la sesión |
| Salidas de SolarCare | `/var/lib/solarcare/salidas` | Directorio de registros y alertas |
| Servicio detector | `solarcare-detector.service` | Utilizado en el flujo funcional |
| Temporizador del agente | `solarcare-agent.timer` | Activo en la integración probada |
| Servicio del agente | `solarcare-agent.service` | Análisis completado |
| Servicio de Ollama | `ollama.service` | Modelos locales disponibles |
| Archivos de modelos | `/var/lib/ollama/models` | Modelos copiados a la Raspberry Pi |
| Aplicación Flask | `/opt/solarcare/web/app.py` | Dashboard y chat funcionales |
| Servicio web | `solarcare-web.service` | Servidor accesible por navegador |
| Ajuste del servicio web | `/etc/systemd/system/solarcare-web.service.d/override.conf` | Corrección de ruta con espacios |

**Nota de reproducibilidad:** la presencia de servicios y archivos en el sistema en ejecución **no demuestra por sí sola** que estén incluidos en las recetas o en la imagen original de Yocto. Es necesario distinguir qué se incorporó durante la compilación y qué se configuró manualmente después del arranque.

## 5. Registro de actividades y resultados del 12 de noviembre de 2026

### 5.1. Arranque y conectividad de Raspberry Pi

**Objetivo:** comprobar que la imagen Linux generada con Yocto arranca y permite trabajar en la Raspberry Pi real.

**Resultado:** se logró iniciar la Raspberry Pi, acceder a su terminal como `root` y establecer conexión SSH desde Ubuntu. Se utilizó la dirección `10.42.0.113`. La computadora anfitriona tenía la dirección `10.42.0.1` en el enlace compartido.

**Pendiente:** documentar evidencia del arranque en frío y comprobar que los servicios y la red quedan operativos después de un reinicio completo.

### 5.2. Acceso a los CSV del SESLAB

**Objetivo:** leer los datos del inversor 2 desde el origen compartido, sin modificar los registros originales.

**Resultado:** se accedió a `//<IP_SERVIDOR_SESLAB>/<RECURSO_COMPARTIDO>` mediante SMB y se consultó el CSV diario del inversor 2 bajo `/var/lib/solarcare/datos`. Se mantuvo la modalidad de lectura (`ro`).

**Limitación:** no se configuró ni verificó un montaje SMB automático mediante `fstab` o una unidad `systemd` de montaje. El acceso también depende de la conectividad disponible hacia el servidor del SESLAB.

### 5.3. Detector y publicación de anomalías

**Objetivo:** comprobar la detección de eventos eléctricos a partir de las mediciones reales.

**Resultado:** el sistema registró una interrupción de generación correspondiente al **12/11/2026, 09:29:20**, con identificador de evento **`ce2d59a7`**. El flujo observado incluyó lectura de CSV, detección, deduplicación y disponibilidad del evento para su interpretación y visualización.

**Importante:** esta prueba demuestra el caso de interrupción de generación. **No valida automáticamente** los demás tipos de anomalía previstos (caída de la aplicación de monitoreo con CSV actualizándose, ausencia de datos nuevos y reducción sostenida de corriente DC).

### 5.4. Ollama y modelos locales

**Objetivo:** ejecutar modelos de lenguaje en la Raspberry Pi, sin depender de un servicio de inferencia remoto.

**Resultado:** el servicio `ollama.service` funcionó en la Raspberry Pi con API local en `127.0.0.1:11434`; el directorio de modelos fue `/var/lib/ollama/models`. Se comprobó la presencia de `tev1:0.8b` y `qwen3:1.7b` mediante `ollama list` y una consulta directa a Tev1. Los modelos se copiaron a la Raspberry Pi desde el entorno de preparación.

**Limitación:** que Ollama funcione en localhost no constituye por sí solo una prueba formal de operación sin Internet. Tampoco confirma la implementación de la API o flujo **JEV** solicitado en la orientación del profesor.

### 5.5. Agente de IA y análisis de un evento

**Objetivo:** verificar que el agente interpreta una alerta producida por el detector.

**Resultado observado en los registros:**

- Inicio de ejecución del agente: **16:04:42**.
- Finalización de análisis del evento `ce2d59a7`: **16:10:12**.
- Tiempo transcurrido aproximado: **5 min 30 s**.
- Resultado del agente: evento marcado como **completo**.
- Valor de clasificación/priorización mostrado para Tev1: **0.5715**.
- Interpretación de Qwen3: disponible posteriormente en el dashboard.

El tiempo observado indica que la inferencia local puede ser lenta para un uso interactivo. Se recomienda medir duración, CPU, memoria y temperaturas en una prueba de rendimiento específica antes de afirmar que el sistema cumple objetivos de latencia.

### 5.6. Dashboard Flask: corrección de ruta de CSV

**Problema:** la variable de entorno que contiene el directorio del inversor incluía un espacio (`Inversor 2`) y la configuración del servicio no preservaba correctamente el valor.

**Corrección aplicada:** se utilizó un archivo de sobreescritura de systemd:

```text
/etc/systemd/system/solarcare-web.service.d/override.conf
```

con la asignación de entorno entre comillas:

```ini
Environment="SOLARCARE_CSV_RAIZ=/var/lib/solarcare/datos/Inversor 2"
```

**Resultado:** el servicio web pudo usar correctamente la ruta de los CSV del inversor 2.

**Pendiente:** incorporar el ajuste a la configuración versionada y al procedimiento de despliegue; no depender únicamente de una modificación manual en el dispositivo.

### 5.7. Dashboard Flask: corrección de fecha predeterminada

**Problema:** la ruta `/api/estado` podía recorrer directorios al no recibir una fecha, provocando una respuesta lenta o bloqueada.

**Corrección aplicada:** se modificó `/opt/solarcare/web/app.py` para usar la fecha actual cuando no se recibe una fecha válida. La expresión registrada fue:

```python
return jsonify(_dashboard(_safe_date(provided) or datetime.now().strftime("%Y-%m-%d")))
```

Se creó un respaldo `app.py.bak` antes de esta modificación.

**Resultado:** el dashboard pudo cargar y mostrar las mediciones y alertas correspondientes.

### 5.8. Dashboard: visualización de datos

**Resultado observado:** el dashboard accesible en `http://10.42.0.113:8091` presentó gráficas, mediciones y el evento registrado. Durante la sesión se visualizaron, entre otros valores, **56.3 kW**, **660.3 V**, **21.70 A** y una estimación de energía de **151.4 kWh**.

Estos números corresponden a una **captura del estado observado durante las pruebas**; no deben tratarse como especificaciones nominales, valores permanentes ni mediciones validadas para cualquier instante.

### 5.9. Chat Qwen3: diagnóstico y corrección de tiempo de espera

**Problema inicial:** la interfaz mostraba **«QWEN3 · SIN CONEXIÓN»**. La solicitud al servidor web devolvía un error HTTP 503 y el registro de Ollama mostró un procesamiento largo de la petición `/api/chat`, con un error 500 después de aproximadamente 1 min 40 s. En el código Flask, la solicitud a Ollama tenía `urlopen(req, timeout=100)`.

**Corrección aplicada:** se amplió el tiempo de espera a **600 segundos** y se reinició el servicio web. Se guardó un respaldo `app.py.bak_chat`.

**Configuración observada de la petición:**

```python
# Fragmento conceptual de la configuración observada
url = f"{OLLAMA_URL}/api/chat"
body = {
    "model": CHAT_MODEL,       # qwen3:1.7b
    "messages": messages,
    "stream": False,
    "think": False,
    "keep_alive": 0,
    "options": {"temperature": 0.2, "num_predict": 600},
}
# urlopen(req, timeout=600)
```

**Resultado:** el chat volvió a responder y permitió realizar consultas técnicas sobre el evento detectado.

**Advertencia:** ampliar el timeout evita un fallo prematuro, pero **no acelera la inferencia**. Conviene estudiar el número de tokens, el contexto enviado, la configuración de Ollama y la carga de memoria/CPU.

### 5.10. Preguntas de validación al chat

Se hicieron consultas sobre el evento de las **09:29**:

1. **¿Qué ocurrió con el inversor 2 a las 09:29?** El modelo describió una interrupción de generación y la caída de la potencia AC y las corrientes DC a cero; diferenció la observación de la causa física no demostrada.
2. **¿Cuáles podrían ser las causas?** El modelo propuso hipótesis técnicas (por ejemplo, control del inversor, red o protecciones), sin que estas constituyan un diagnóstico confirmado.
3. **¿Qué evidencia existe?** El modelo mencionó potencia AC de **0 W**, corrientes DC de **0 A** y tensiones DC de **842.5 V**, **827.7 V**, **824.8 V** y **826.4 V**.

**Limitación importante:** estas respuestas son salidas del modelo y **no se contrastaron completamente con el CSV original** durante la sesión. En particular, la afirmación de que las tensiones aumentaron significativamente requiere comparar mediciones anteriores y posteriores; no basta con los valores aislados. El chat debe presentar hipótesis como hipótesis, no como causas verificadas.

### 5.11. Revisión de cumplimiento frente a la orientación del profesor

Se comparó el prototipo con el documento **«Orientación para el II Proyecto: Sistemas Inteligentes de Borde – EdgeAI»**. La orientación pide una aplicación relevante con LLM/JEV, arquitectura, aplicaciones, dependencias, recetas Yocto, imagen Linux para Raspberry Pi, instalación, procedimiento reproducible, demostración y bitácoras individuales.

**Fortalezas demostradas:** caso de uso fotovoltaico concreto, Raspberry Pi con Yocto, datos reales, detector, agente local, dashboard y chat.

**Aspectos no verificados o incompletos:** uso efectivo de **JEV** (incluida la referencia del enunciado a `/v1/systemone`), recetas y dependencias integradas a la imagen, guía paso a paso de compilación e instalación, evidencia de funcionamiento tras reinicio, demostración formal de casos de uso, bitácoras y estado del repositorio público.

**Observación del enunciado:** el documento menciona Raspberry Pi para la imagen y, en otro apartado, «JETSON NANO» para la demostración. Esta discrepancia debe aclararse con el profesor si afecta la evaluación; no se interpreta como cambio automático de plataforma.

### 5.12. Evaluación de la función de análisis manual de CSV históricos

Se **analizó la factibilidad**, pero **no se modificó el programa ni el dashboard** para implementarla.

El detector `/opt/solarcare/monitor_diario_solarcare.py` ya importa `argparse` y define estos argumentos:

```text
--raiz
--fecha
--continuo
--intervalo
--verificar-datos
--ahora
--publicar-estados
--salidas
--seguimiento-estado
--publicar-electricas
```

La función existente:

```python
def archivo_del_dia(raiz, dia):
    nombre = dia.isoformat()
    return raiz / nombre / f"{nombre}.csv"
```

permite construir la ruta de un archivo por fecha. Se comprobó, por inspección de código, que existe un parámetro `--fecha`, pero **no se verificó todavía que una ejecución sin `--continuo` procese todo el CSV histórico ni que no interfiera con el estado del monitoreo automático**.

**Estimaciones preliminares, no compromisos:**

| Alternativa | Alcance | Tiempo estimado |
|---|---|---|
| A | Análisis desde terminal seleccionando fecha | 20–45 min, sujeto a verificar el flujo |
| B | Selector de fecha y botón en el dashboard | 1.5–3 h |
| C | Carga de cualquier CSV desde navegador | 3–5 h |

**Decisión de la sesión:** no implementar esta funcionalidad por ahora. Priorizar los requisitos de integración y validación del prototipo. El análisis manual permanece como requisito de la propuesta del equipo (RF-01/RF-04) pendiente o posible mejora futura; no debe marcarse como completado.

## 6. Estado de requisitos y evidencia

| Requisito o capacidad | Estado al 12/11/2026 | Evidencia / limitación |
|---|---|---|
| Imagen Yocto en Raspberry Pi | Verificado parcialmente | Arranque en hardware real; falta reproducibilidad completa |
| Red y acceso SSH | Verificado en sesión | IP `10.42.0.113` |
| Lectura CSV del SESLAB | Verificado en sesión | SMB de solo lectura; montaje manual |
| Detector de interrupción de generación | Verificado | Evento `ce2d59a7`, 09:29:20 |
| Detección de otros tipos de anomalías | Pendiente de pruebas | No se observaron pruebas completas |
| Deduplicación / registro de eventos | Observado en flujo funcional | Requiere prueba de regresión documentada |
| Ollama y modelos locales | Verificado en sesión | `tev1:0.8b`, `qwen3:1.7b` |
| Agente Tev1 → Qwen3 | Verificado en evento | Análisis marcado «completo» |
| Dashboard y gráficas | Verificado en sesión | Puerto 8091 |
| Chat técnico Qwen3 | Verificado tras corrección | Timeout 600 s; latencia alta |
| Integración JEV requerida por profesor | No verificada | Revisar código y API real utilizada |
| Análisis manual de CSV | Evaluado; no implementado | `--fecha` existe; flujo no validado |
| Detector operativo con Ollama detenido | Pendiente de prueba | Requisito de independencia |
| Funcionamiento sin Internet | Pendiente de prueba formal | Inferencia local observada |
| Reinicio autónomo y servicios persistentes | Pendiente | Incluye montaje SMB |
| Recetas y guía de Yocto | Recetas presentes; auditoría y guía pendientes | Distinguir imagen vs cambios manuales |
| Repositorio público y bitácoras | Repositorio localizado; bitácoras pendientes de verificación | Requisito del curso |

## 7. Cambios efectuados y control de versiones

| Archivo / configuración | Cambio realizado | Respaldo o consideración |
|---|---|---|
| `solarcare-web.service.d/override.conf` | Ruta `SOLARCARE_CSV_RAIZ` entre comillas | Conservar en despliegue reproducible |
| `/opt/solarcare/web/app.py` | Fecha predeterminada de `/api/estado` | `app.py.bak` |
| `/opt/solarcare/web/app.py` | `urlopen` con timeout de 600 s para chat | `app.py.bak_chat` |
| Montaje SMB en `/var/lib/solarcare/datos` | Acceso manual `ro` a datos del SESLAB | No persistente verificado |
| Modelos en `/var/lib/ollama/models` | Modelos locales disponibles en Pi | Confirmar inclusión en imagen/instalador |

**No se modificaron los CSV originales del SESLAB.** No se realizó una implementación del modo manual.

## 8. Guía rápida de verificación posterior (comandos de consulta)

Los siguientes comandos son una **guía propuesta para una sesión posterior**; no todos constituyen pruebas ya ejecutadas el 12/11/2026.

### 8.1. Estado de servicios

```bash
systemctl status solarcare-detector.service solarcare-agent.timer solarcare-web.service ollama.service --no-pager
```

### 8.2. Montaje y acceso a los CSV

```bash
mount | grep '/var/lib/solarcare/datos'
ls -l '/var/lib/solarcare/datos/Inversor 2/2026-11-12/2026-11-12.csv'
```

### 8.3. Modelos locales

```bash
ollama list
```

### 8.4. Eventos y registros

```bash
journalctl -u solarcare-agent.service -n 60 --no-pager
journalctl -u solarcare-web.service -n 60 --no-pager
ls -l /var/lib/solarcare/salidas
```

### 8.5. Dashboard

Abrir desde el navegador de Ubuntu: `http://10.42.0.113:8091` (si la Raspberry conserva esa dirección).

### 8.6. Comprobación de JEV sin modificar archivos

```bash
grep -RniE 'systemone|jev|tev1|api/chat|api/generate|OLLAMA_URL' /opt/solarcare --include='*.py'
```

La búsqueda solo muestra referencias en el código. La conformidad real con JEV debe comprobarse con la API efectivamente utilizada y una prueba funcional específica.

## 9. Riesgos y limitaciones identificados

1. **Montaje SMB manual:** el detector puede quedar sin datos después de reiniciar si no se restaura el recurso compartido.
2. **Dependencia de red hacia el SESLAB:** la lectura de CSV requiere que el servidor y la ruta de red estén disponibles.
3. **Tiempo de inferencia:** se observaron varios minutos para el análisis de un evento y tiempos elevados en el chat.
4. **Cambios posteriores al arranque:** las correcciones de Flask, systemd y modelos deben incorporarse a una instalación reproducible.
5. **Verificación de JEV:** el uso de Tev1 y Ollama no demuestra por sí mismo el uso del mecanismo JEV pedido por el profesor.
6. **Cobertura de pruebas:** solo se confirmó directamente un caso de interrupción de generación; otros eventos y fallos necesitan ensayos específicos.
7. **Calidad de las respuestas de IA:** el modelo puede formular hipótesis plausibles sin evidencia suficiente; se requiere cotejo con CSV y reglas de presentación de incertidumbre.
8. **Análisis manual pendiente:** `--fecha` existe, pero la funcionalidad completa no está validada ni disponible desde el dashboard.

## 10. Prioridades para la siguiente sesión

**Prioridad 1 — Cumplimiento de la asignación:** revisar el código del agente para establecer si utiliza JEV y documentar el resultado; auditar recetas Yocto, dependencias y pasos de construcción e instalación.

**Prioridad 2 — Autonomía y recuperación:** reiniciar la Raspberry Pi y comprobar red, servicios, modelos, dashboard y montaje de datos; definir un montaje SMB persistente sin guardar credenciales en el repositorio.

**Prioridad 3 — Robustez:** detener Ollama temporalmente en una prueba controlada para verificar que el detector sigue generando alertas; comprobar ausencia de Internet y casos de datos ausentes o corruptos.

**Prioridad 4 — Validación funcional:** cotejar el evento de las 09:29 con las filas reales del CSV, documentar pruebas para las demás categorías de anomalía y registrar tiempos y recursos.

**Prioridad 5 — Entrega:** consolidar repositorio público, bitácoras individuales, capturas, casos de uso y guía reproducible de Yocto. El modo manual queda aplazado hasta cubrir estas prioridades.

## 11. Evidencias que conviene conservar

- Captura de arranque de la Raspberry Pi con Yocto y versión de sistema.
- Dirección de red y conexión SSH funcional.
- Evidencia de montaje SMB `ro` y existencia del CSV diario.
- Registro del evento `ce2d59a7` y sus marcas temporales.
- `ollama list` con ambos modelos.
- Registro de ejecución del agente y su resultado «completo».
- Dashboard mostrando gráfica, alerta e interpretación.
- Chat Qwen3 respondiendo preguntas sobre el evento.
- Configuraciones versionadas de systemd, Flask y recetas Yocto.
- Capturas de compilación de la imagen y procedimiento de grabación en microSD.

## 12. Conclusión

La sesión permitió **validar por primera vez el flujo integrado de SolarCare AI sobre la Raspberry Pi con Yocto**: lectura de datos reales del SESLAB, detección de un evento, análisis local con Tev1/Qwen3, visualización y consulta mediante chat. Los problemas encontrados en la ruta del CSV, la fecha predeterminada del dashboard y el timeout del chat fueron identificados y corregidos en el entorno de prueba.

El siguiente objetivo no es añadir funciones de interfaz, sino **convertir el prototipo funcional en una implementación reproducible, autónoma y demostrable**. La documentación debe mantener separadas las capacidades verificadas, las configuraciones manuales, las pruebas aún pendientes y los requisitos explícitos de la orientación del profesor.

---

### Fuentes internas de referencia

- Orientación del profesor: *Orientación para el II Proyecto: Sistemas Inteligentes de Borde – EdgeAI*, II semestre 2026.
- Propuesta del equipo: *SolarCare AI: propuesta de diseño de un sistema embebido inteligente para el análisis de anomalías fotovoltaicas*.
- Evidencia de la sesión: comandos, salidas de terminal, registros de systemd/Ollama, capturas del dashboard y fragmentos de código compartidos el 12 de noviembre de 2026.

**Nota de trazabilidad:** los resultados aquí descritos provienen de la sesión de trabajo. Las acciones propuestas para futuras pruebas están identificadas explícitamente como pendientes.

## 13. Estado del repositorio Git al 12/11/2026

Se verificó el repositorio público `VeroC25/Project_2_Embebidos`, rama `main`. Contiene la propuesta de diseño, una capa `yocto/meta-solarcare`, la receta de imagen `solarcare-image.bb`, la receta de Ollama `ollama_0.40.13.bb`, la receta de la aplicación `solarcare_1.0.bb`, unidades systemd del detector y agente, y una receta de almacenamiento. Por tanto, **sí existen recetas de Yocto versionadas**; el pendiente es **auditar su cobertura y reproducibilidad**.

En la revisión, la receta `solarcare_1.0.bb` instala unidades systemd, pero no se observó que empaquete los scripts Python del detector/agente ni la aplicación Flask; tampoco se encontró una unidad `solarcare-web.service` en el árbol publicado. Es necesario comparar el contenido de la imagen compilada con las modificaciones manuales realizadas en la Raspberry Pi y versionar los archivos faltantes antes de afirmar que la compilación reproduce todo el prototipo.

**Privacidad del repositorio público:** se sustituyeron en este documento la IP del servidor interno del SESLAB y el nombre del recurso SMB por marcadores de configuración. Las credenciales no deben incluirse en Git.
