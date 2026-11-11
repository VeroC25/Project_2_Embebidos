# SolarCare AI — Dashboard v2 (tema claro)

Rediseño visual siguiendo la referencia de interfaz clara con tarjetas verde oliva, crema y un panel de conversación. **Se conserva la familia tipográfica de la versión azul**: `Inter, Segoe UI, Roboto, Ubuntu, Arial, sans-serif`, usando las fuentes disponibles en el sistema (sin descargar tipografías).

## Instalación en Ubuntu

Descomprimir `interfaz_solarcare_v2/` dentro de `~/Ollama_proy`, junto a `detector_solarcare.py`, `salidas/`, etc. La carpeta `interfaz_solarcare` (v1) permanece intacta.

```bash
cd ~/Ollama_proy
source .venv/bin/activate
python -m pip install -r interfaz_solarcare_v2/requirements.txt
SOLARCARE_CSV="$(pwd)/simulacion_interrupcion.csv" python interfaz_solarcare_v2/app.py
```

Abrir **http://127.0.0.1:8091/** en Firefox (la v1 usa 8090 y Jenkins, 8080). Detener el servidor con `Ctrl+C`.

Si solo se ejecuta `python interfaz_solarcare_v2/app.py` sin configurar `SOLARCARE_CSV`, la aplicación mostrará los archivos en `salidas` si existen. Si no existen ni alertas ni CSV, aparecerá **DEMO** con valores ilustrativos, no datos reales.

## Qué lee, sin modificar el detector

- `SOLARCARE_SALIDAS` (opcional): directorio de `alertas_anomalias.csv` y `resultados_ia/*.json` (por defecto `~/Ollama_proy/salidas`).
- `SOLARCARE_CSV` (opcional): ruta a un CSV particular del inversor 2.
- `SOLARCARE_CSV_RAIZ` (opcional): ruta a una raíz con subcarpetas `YYYY-MM-DD/YYYY-MM-DD.csv`; permite cambiar la fecha desde el selector. Prioridad sobre `SOLARCARE_CSV`.
- La potencia, las tensiones y las corrientes se obtienen de las mediciones existentes. La **energía estimada** se integra por trapecios, sin interpolar intervalos de más de 15 minutos; no es energía certificada/facturada.
- Los eventos se filtran por la fecha mostrada. El marcador en la gráfica aparece solo si el tiempo del evento corresponde a una muestra de esa fecha (tolerancia de 15 minutos).
- Leer un CSV **no verifica** que el inversor esté actualmente operando ni que los datos estén frescos.

## Chat experimental con Qwen3

El chat ya incluye un enlace independiente a la API local de Ollama, sin alterar `agente_solarcare.py`, el detector ni la cola. Necesitás Ollama ejecutándose con `qwen3:1.7b` instalado; si no está disponible, la interfaz lo avisará. Se envía a Qwen3 el evento seleccionado y hasta 6 turnos recientes de contexto. La conversación no controla equipos ni cambia CSV.

Variables opcionales:

```bash
SOLARCARE_OLLAMA_URL=http://127.0.0.1:11434
SOLARCARE_CHAT_MODEL=qwen3:1.7b
SOLARCARE_PORT=8091
```

Ejemplo de comprobación local del modelo:

```bash
ollama list
ollama ps
```

No se ha medido la capacidad de respuesta del chat en Raspberry Pi/Yocto, y el servidor Flask integrado es solo para desarrollo: en el despliegue, configurar un servidor WSGI y acceso de red controlado. No exponer la interfaz ni la API Ollama públicamente sin autenticación y restricciones de red.

## Archivos

- `app.py`: servidor Flask, lectura de CSV/alertas y endpoint `/api/chat`.
- `templates/index.html`: estructura del dashboard.
- `static/styles.css`: diseño visual, responsive, conserva tipografía de v1.
- `static/app.js`: gráfico, selección de alertas, filtros de fecha y chat.
- `requirements.txt`: Flask.

## Nota técnica

Esta interfaz es una **herramienta de visualización y apoyo** del SESLAB. Las interpretaciones de IA no son diagnósticos confirmados de fallas. Las pruebas del chat deberán realizarse en el Ubuntu local y luego en Yocto cuando se verifique Ollama en el dispositivo objetivo.
