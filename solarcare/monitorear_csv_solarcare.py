"""Supervisión LOCAL de un CSV SolarCare AI: sólo lectura de la fuente.

Para probar sin publicar: python monitorear_csv_solarcare.py simulacion_interrupcion.csv
Para supervisar cambios: python monitorear_csv_solarcare.py archivo.csv --continuo
Para publicar en la cola (sólo con autorización): agregar --publicar.
"""
import argparse
import time
from pathlib import Path

from detector_solarcare import leer_csv, detectar_anomalias


def inspeccionar(ruta: Path, publicar: bool = False):
    mediciones = leer_csv(ruta)
    eventos = detectar_anomalias(mediciones)
    print(f"Archivo: {ruta.name} | mediciones: {len(mediciones)} | candidatos: {len(eventos)}", flush=True)
    for evento in eventos:
        etiqueta = evento.get("subtipo", evento["evento"])
        print(f"  - {etiqueta} | {evento['inicio_evento']}", flush=True)
        if publicar:
            from publicacion_unica import publicar_evento_unico
            resultado = publicar_evento_unico(evento)
            print("    → " + ("Ya registrada" if resultado["duplicado"] else "Alerta nueva"), flush=True)
    return eventos


def main():
    parser = argparse.ArgumentParser(description="Monitorea un CSV local sin modificarlo")
    parser.add_argument("archivo", type=Path, help="CSV local o copia de prueba")
    parser.add_argument("--continuo", action="store_true", help="Vigilar cambios posteriores")
    parser.add_argument("--intervalo", type=float, default=10.0, help="Segundos entre consultas (predeterminado: 10)")
    parser.add_argument("--publicar", action="store_true", help="Registrar alertas y encolarlas para IA")
    args = parser.parse_args()
    if args.intervalo <= 0:
        parser.error("--intervalo debe ser mayor que cero")

    ultima_version = None
    print("Modo:", "continuo" if args.continuo else "una ejecución", "| publicación:", "SÍ" if args.publicar else "NO", flush=True)
    while True:
        try:
            datos = args.archivo.stat()
            version = (datos.st_mtime_ns, datos.st_size)
            if version != ultima_version:
                try:
                    inspeccionar(args.archivo, publicar=args.publicar)
                except (OSError, ValueError) as exc:
                    print(f"Aviso: archivo todavía no procesable ({exc}). Se reintentará si está en modo continuo.", flush=True)
                else:
                    ultima_version = version
        except OSError as exc:
            print(f"Aviso: no se puede acceder al archivo ({exc}).", flush=True)
        if not args.continuo:
            break
        try:
            time.sleep(args.intervalo)
        except KeyboardInterrupt:
            print("\nSupervisión detenida por el usuario.")
            break


if __name__ == "__main__":
    main()
