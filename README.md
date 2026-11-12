# SolarCare AI — Proyecto 2 de Sistemas Embebidos

Sistema embebido para la detección e interpretación local de anomalías fotovoltaicas, desarrollado para el **Taller de Sistemas Embebidos** del Instituto Tecnológico de Costa Rica (TEC).

**Equipo:** Marycruz Fallas Barquero y Verónica Cambronero Solano.

## Descripción

SolarCare AI complementa la plataforma de monitoreo del SESLAB. Su caso de uso inicial es el inversor 2: analiza mediciones en CSV, genera alertas mediante un detector independiente y permite interpretarlas con modelos locales de IA ejecutados con Ollama en una Raspberry Pi 4 (8 GB) con Linux generado mediante Yocto Project.

El prototipo probado el **12 de noviembre de 2026** integra detector, agente de IA, dashboard Flask y chat técnico con Qwen3. La operación tras reinicio, la reproducción completa desde recetas Yocto y la integración JEV aún requieren verificación.

## Documentación

- **[Estado de integración, pruebas, correcciones y pendientes — 12/11/2026](docs/estado-integracion-2026-11-12.md)**: registro técnico de la sesión, comandos de consulta, evidencias, riesgos y análisis de viabilidad del modo manual de CSV.
- **[Capa Yocto meta-solarcare](yocto/meta-solarcare/)**: recetas de imagen, Ollama, servicios de SolarCare y almacenamiento.
- **Propuesta de diseño**: PDF disponible en la raíz del repositorio.

## Estado y próximos pasos

- **Verificado en sesión:** arranque de la Raspberry Pi, acceso de solo lectura a datos del SESLAB, detección de un evento de interrupción de generación, ejecución local de Tev1 y Qwen3, dashboard y chat.
- **Pendiente:** revisar JEV, incorporar al control de versiones los scripts y ajustes que se aplicaron manualmente, validar recetas y procedimiento reproducible, montaje SMB persistente, reinicio autónomo, pruebas de fallos y bitácoras.
- **Análisis manual de CSV:** se evaluó su viabilidad, pero **no se implementó**.

> **Nota:** Las recetas presentes en Git no deben confundirse con una instalación completamente reproducible. La documentación separa lo verificado de las tareas pendientes. No publicar credenciales ni detalles de acceso privado al SESLAB.
