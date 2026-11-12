# Plantilla de evidencia de prueba — SolarCare AI

> **Uso:** copiar esta plantilla con un nombre descriptivo, por ejemplo `Y-05_tev1_qwen_raspberry_pi.md`. El contenido está **sin ejecutar**; completar únicamente con resultados observados y archivos autorizados.

## Identificación

| Campo | Registro |
| --- | --- |
| ID del caso | Por completar (por ejemplo, Y-05) |
| Nombre | Por completar |
| Requisito asociado | Por completar (RF-…, RNF-…) |
| Fecha y hora de ejecución | Por completar |
| Responsable | Por completar |
| Estado | **No ejecutada** |
| Commit probado | Por completar (`git rev-parse --short HEAD`) |
| Entorno | Ubuntu / Raspberry Pi 4 con Yocto / infraestructura SESLAB (especificar) |
| Versiones relevantes | Python, Ollama, Tev1, Qwen3, imagen Yocto, según el caso |

## Objetivo de la prueba

Describir qué se desea validar y por qué este resultado permite comprobar el requisito. No confundir instalación con operación correcta.

## Condiciones previas

- Equipo utilizado y sistema operativo: por completar.
- Servicios que deben estar activos: por completar.
- Datos de entrada: **sintéticos o autorizados**, descritos sin publicar información institucional restringida.
- Preparación o configuración de rutas: por completar.
- Dependencias o autorizaciones: por completar.

## Procedimiento reproducible

Indicar comandos o pasos numerados tal como fueron ejecutados, evitando incluir contraseñas, claves, tokens, direcciones privadas de red o archivos internos.

1. Por completar.
2. Por completar.
3. Por completar.

## Resultado esperado

Expresar criterios verificables antes de ejecutar. Ejemplo de formato: «El evento queda registrado en el CSV independiente y conserva el mismo `id_evento` al producirse el resultado JSON».

## Resultado observado

**Pendiente de ejecutar.**

Registrar datos observados concretos, nombres de archivos de salida autorizados, códigos de error, fechas y cualquier desviación del resultado esperado. No sustituir la observación por una descripción del código o por una intención de diseño.

## Métricas (si aplica)

| Métrica | Valor observado | Unidad | Herramienta / método |
| --- | --- | --- | --- |
| Duración total | Pendiente | s | Por completar |
| Duración de inferencia Tev1 | Pendiente | s | Por completar |
| Duración de inferencia Qwen3 | Pendiente | s | Por completar |
| Memoria máxima | Pendiente | MiB | Por completar |
| Uso de CPU | Pendiente | % | Por completar |
| Espacio libre de almacenamiento | Pendiente | GiB | Por completar |
| Retraso entre medición y CSV disponible | Pendiente | min | Por completar |

Dejar explícito «no aplica» cuando una métrica no corresponda al caso; **no completar valores estimados como si fueran observados**.

## Evidencias adjuntas

- Captura o log: pendiente.
- Ruta relativa dentro del repositorio, si está autorizado publicar: pendiente.
- Hash o referencia a un artefacto externo autorizado: pendiente.

Las evidencias deben estar anonimizadas. **No subir datos originales del SESLAB, credenciales, IP privadas ni registros internos no autorizados.**

## Evaluación

- **Estado final:** No ejecutada / Aprobada / Fallida / Bloqueada.
- **Criterio utilizado:** por completar.
- **Desviaciones encontradas:** por completar.
- **Acción correctiva o siguiente prueba:** por completar.
- **Repetición requerida:** Sí / No / Pendiente.

## Referencias

- [Plan general de pruebas y validación](../08_pruebas_y_validacion.md)
- [Matriz de trazabilidad](../02_matriz_requerimientos.md)
