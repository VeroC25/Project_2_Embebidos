# SolarCare AI — Recuperación en otra Raspberry Pi

**Respaldo:** 12 de noviembre de 2026. **Objetivo:** reproducir el código y servicios que estaban funcionando en la Raspberry Pi original. **No es evidencia de que una nueva imagen haya sido compilada o probada.**

## Qué está versionado

- Los 10 scripts Python de `/opt/solarcare` (detector, monitor, puente, agente y trabajador).
- Dashboard Flask: `web/app.py`, `web/static/app.js`, `web/static/styles.css` y `web/templates/index.html`.
- Unidades `solarcare-detector.service`, `solarcare-agent.service`, `solarcare-agent.timer` y `solarcare-web.service`, además del override de la raíz de CSV.
- Receta `solarcare_1.0.bb` que instala los archivos anteriores al construir una nueva imagen con la capa `meta-solarcare`.
- El archivo `ollama.service` ya estaba versionado en la receta de Ollama y coincide con el respaldo.

**No se versionan:** contraseñas, archivos CSV del SESLAB, modelos de Ollama, bibliotecas binarias, archivos `.pyc`, backups de código ni contenido de `/var/lib/solarcare/salidas`. El enlace simbólico `/opt/solarcare/salidas` apunta a `/var/lib/solarcare/salidas`.

## Opción A — Recuperar en una Raspberry Pi que ya tiene la imagen base

1. Conectá la Raspberry Pi 4 (8 GB) a la red y verificá que SSH funciona. Su IP puede cambiar.
2. Desde Ubuntu, cloná el repositorio y entrá en su directorio:

   ```bash
   git clone https://github.com/VeroC25/Project_2_Embebidos.git
   cd Project_2_Embebidos
   ```

3. Copiá código y servicios a la nueva Pi (sustituí la IP):

   ```bash
   bash scripts/deploy-to-pi.sh root@IP_DE_LA_RASPBERRY
   ```

4. Comprobá que el Python del dispositivo puede importar los paquetes externos:

   ```bash
   ssh root@IP_DE_LA_RASPBERRY 'python3 -c "import flask, ollama; print("Dependencias Python disponibles")"'
   ```

   Si falla, **no inicies todavía el sistema**. La imagen de Yocto debe incluir Flask y el cliente Python `ollama`, o deben instalarse por un procedimiento compatible con esa imagen. `requirements.txt` documenta los nombres, **no garantiza su disponibilidad en Yocto**. No se comprobó el nombre de los paquetes BitBake correspondientes.

5. Verificá que Ollama y ambos modelos estén instalados y disponibles:

   ```bash
   ssh root@IP_DE_LA_RASPBERRY 'systemctl status ollama --no-pager; ollama list'
   ```

   Modelos requeridos: `tev1:0.8b` y `qwen3:1.7b`. **No están incluidos en Git**. El endpoint `/v1/systemone` utilizado por Tev1 debe existir en la versión de Ollama/JEV instalada: el repositorio por sí solo **no garantiza** esa compatibilidad.

6. Configurá el acceso **de solo lectura** a los CSV del SESLAB en `/var/lib/solarcare/datos`. La ruta esperada del caso inicial es `/var/lib/solarcare/datos/Inversor 2/AAAA-MM-DD/AAAA-MM-DD.csv`. **No pongás credenciales en Git**. El montaje SMB y sus permisos deben configurarse con el administrador de la red. La nueva Pi puede tener IP diferente; no depende de la IP de la Pi original.

7. Verificá que el archivo del día esté disponible y que el directorio de salidas exista:

   ```bash
   ssh root@IP_DE_LA_RASPBERRY 'ls -l "/var/lib/solarcare/datos/Inversor 2"; mkdir -p /var/lib/solarcare/salidas'
   ```

8. Habilitá y arrancá los servicios **después** de configurar datos y modelos:

   ```bash
   ssh root@IP_DE_LA_RASPBERRY 'systemctl enable --now solarcare-detector.service solarcare-agent.timer solarcare-web.service'
   ```

   Comprobá `systemctl status solarcare-detector solarcare-agent.timer solarcare-web ollama --no-pager`, y consultá `journalctl -u solarcare-web -n 30 --no-pager`. El dashboard escucha en `http://IP_DE_LA_RASPBERRY:8091` en la red local.

## Opción B — Nueva imagen Yocto

La receta `yocto/meta-solarcare/recipes-apps/solarcare/solarcare_1.0.bb` ahora contiene instrucciones para empaquetar **los archivos recuperados del dispositivo** en `/opt/solarcare` y las unidades systemd. Para que una nueva imagen arranque de forma autónoma aún hace falta:

- Verificar que la compilación BitBake incluye correctamente los archivos, dependencias Flask/ollama y el sistema de archivos persistente.
- Garantizar la disponibilidad de los binarios ARM64 de Ollama y los modelos en el dispositivo.
- Resolver acceso SMB a datos, credenciales fuera del repositorio y montaje automático de solo lectura.
- Verificar el endpoint Tev1 `/v1/systemone` y la integración JEV.
- Probar **desde cero** la nueva imagen en una microSD separada; **no sobrescribir** la microSD funcional.

## Verificación y límites

- El respaldo se extrajo y se revisó para excluir credenciales y archivos temporales; se comprobó sintaxis de Python de los scripts, pero **no se ejecutaron pruebas funcionales en una nueva Raspberry Pi**.
- Las correcciones del dashboard incluyen el override `SOLARCARE_CSV_RAIZ` y `urlopen(..., timeout=600)` en `web/app.py`.
- El detector y el agente son procesos separados; el agente se ejecuta periódicamente mediante `solarcare-agent.timer`.
- No hay montaje SMB persistente documentado en el respaldo, ni se guardaron las credenciales.
- No se implementó un modo manual de análisis histórico de CSV.

## Problemas habituales

| Síntoma | Qué comprobar |
| --- | --- |
| Web no abre | `systemctl status solarcare-web`, IP y puerto 8091 |
| Dashboard sin datos | Montaje de solo lectura y variable `SOLARCARE_CSV_RAIZ` |
| No hay interpretaciones IA | `systemctl status ollama`, `ollama list`, `journalctl -u solarcare-agent` |
| Tev1 falla | Compatibilidad de `/v1/systemone` en el motor local |
| Después de reiniciar faltan CSV | Configuración persistente del montaje SMB (pendiente) |
| La nueva imagen no compila | Revisar dependencias BitBake y contenido de `meta-solarcare` |
