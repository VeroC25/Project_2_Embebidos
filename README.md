# SolarCare AI — Proyecto 2 de Sistemas Embebidos

Sistema embebido para la detección e interpretación local de anomalías fotovoltaicas, desarrollado para el **Taller de Sistemas Embebidos** del Instituto Tecnológico de Costa Rica (TEC).

**Equipo:** Marycruz Fallas Barquero y Verónica Cambronero Solano.

## Descripción

SolarCare AI complementa la plataforma de monitoreo del SESLAB. Su caso de uso inicial es el inversor 2: analiza mediciones en CSV, genera alertas mediante un detector independiente y permite interpretarlas con modelos locales de IA ejecutados con Ollama en una Raspberry Pi 4 (8 GB) con Linux generado mediante Yocto Project.

El prototipo probado el **12 de noviembre de 2026** integra detector, agente de IA, dashboard Flask y chat técnico con Qwen3. La operación tras reinicio, la reproducción completa desde recetas Yocto y la integración JEV aún requieren verificación.

## Documentación

- **[Estado de integración, pruebas, correcciones y pendientes — 12/11/2026](docs/estado-integracion-2026-11-12.md)**: registro técnico de la sesión, comandos de consulta, evidencias, riesgos y análisis de viabilidad del modo manual de CSV.
- **[Guía para recuperar SolarCare AI en otra Raspberry Pi](docs/instalacion-otra-raspberry.md)**: transferencia por SSH, servicios, dependencias, modelos y datos.
- **[Código recuperado de la Raspberry Pi](yocto/meta-solarcare/recipes-apps/solarcare/files/solarcare/)**: detector, agente y dashboard Flask.
- **[Capa Yocto meta-solarcare](yocto/meta-solarcare/)**: recetas de imagen, Ollama, aplicación y almacenamiento.
- **Propuesta de diseño**: PDF disponible en la raíz del repositorio.

## Estado y próximos pasos

- **Verificado en sesión:** arranque de la Raspberry Pi, acceso de solo lectura a datos del SESLAB, detección de un evento de interrupción de generación, ejecución local de Tev1 y Qwen3, dashboard y chat.
- **Pendiente:** revisar JEV, validar la nueva receta de aplicación mediante BitBake y comprobar dependencias, modelos y procedimiento reproducible, montaje SMB persistente, reinicio autónomo, pruebas de fallos y bitácoras.
- **Análisis manual de CSV:** se evaluó su viabilidad, pero **no se implementó**.

> **Nota (12/11/2026):** Se respaldaron en Git los scripts, el dashboard y las unidades systemd recuperadas de la Raspberry Pi. La receta de la aplicación fue actualizada para empaquetarlos, pero **no se ha compilado ni validado una nueva imagen**. Para migrar a otro equipo también se requieren las dependencias Flask/ollama, los modelos Tev1/Qwen3 y el acceso de solo lectura a los CSV. No publicar credenciales ni detalles privados del SESLAB.
