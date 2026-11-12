# Documentación técnica — SolarCare AI

La documentación de **SolarCare AI** se mantiene en Markdown para que cada cambio pueda revisarse y trazarse mediante commits y pull requests de GitHub.

## Documentos disponibles

1. [Matriz de trazabilidad y estado de requerimientos](02_matriz_requerimientos.md) — compara los 16 requisitos funcionales y los 8 no funcionales de la propuesta con el desarrollo publicado, especifica evidencia disponible y pendientes de validación.
2. [Arquitectura del sistema](03_arquitectura_del_sistema.md) — describe entornos, componentes, diagramas, interfaces de datos, decisiones de diseño e integración con Yocto, diferenciando evidencias locales y validaciones pendientes.
3. [Implementación del detector y monitoreo de anomalías](04_implementacion_del_detector.md) — lectura y validación de CSV, parámetros actuales, detección de interrupciones y caídas de corriente, ausencia de datos, deduplicación, pruebas y limitaciones.
4. [Integración de inteligencia artificial](05_integracion_inteligencia_artificial.md) — documenta Tev1, Qwen3, Ollama, el procesamiento de cola, los estados ante fallos, el chat contextual y los ensayos pendientes.

## Documentos por desarrollar

| Tema | Contenido mínimo | Estado |
| --- | --- | --- |
| Descripción y alcance del proyecto | Problema, objetivos, alcance y cambios respecto a la propuesta | Por redactar |
| Arquitectura del sistema | Diagrama de componentes, interfaces, archivos y flujo de eventos | **Versión inicial publicada; pendiente de evidencias embebidas** |
| Implementación del detector | Algoritmos, umbrales, estados, deduplicación y justificación | **Versión inicial publicada; calibración y validación embebida pendientes** |
| Agente de IA | Tev1, Qwen3, Ollama, validación y manejo de fallos | **Versión inicial publicada; validación embebida pendiente** |
| Interfaz gráfica | Flask, rutas, dashboard, chat, origen y frescura de los datos | Por redactar |
| Integración embebida | Recetas de Yocto, servicios systemd, despliegue y almacenamiento | Pendiente de evidencias finales |
| Pruebas y resultados | Casos, métodos, comandos, registros, mediciones y capturas | En recopilación |
| Limitaciones y conclusiones | Resultados verificados, requisitos incompletos y trabajo futuro | Por redactar |

## Documento de referencia

La propuesta original de diseño se encuentra en la raíz del repositorio como PDF. Su descripción del problema, requerimientos, arquitectura prevista y plan de integración son el **punto de partida**, pero los documentos de esta carpeta describirán lo **implementado y verificado**.

## Convención de evidencia

Cada prueba incorporada deberá indicar:

- Identificador del requisito o caso de uso.
- Entorno: Ubuntu, Raspberry Pi con Yocto o infraestructura SESLAB.
- Datos utilizados (sin publicar datos internos no autorizados).
- Procedimiento o comando reproducible.
- Resultado esperado y resultado observado.
- Fecha y archivo de evidencia asociado.

El código, las pruebas automatizadas y la interfaz actualmente publicados se encuentran en [software/](../software/). La infraestructura Yocto está en [yocto/](../yocto/).

**Precaución:** no subir IP privadas, contraseñas, claves, registros institucionales no autorizados ni resultados generados que expongan información sensible.
