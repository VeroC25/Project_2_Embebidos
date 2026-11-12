import argparse
import time
from datetime import date
from pathlib import Path

from monitorear_csv_solarcare import inspeccionar
from detectar_ausencia_datos import verificar_actualizacion
from eventos_ausencia_solarcare import crear_evento_ausencia
from seguimiento_estado_datos import actualizar_estado
from publicacion_unica import publicar_evento_unico
from datetime import datetime


def archivo_del_dia(raiz, dia):
    nombre = dia.isoformat()
    return raiz / nombre / f"{nombre}.csv"


def main():
    parser = argparse.ArgumentParser(
        description="Monitor diario de SolarCare AI"
    )

    parser.add_argument(
        "--raiz",
        type=Path,
        default=Path("simulacion_vm/Inversor 2")
    )

    parser.add_argument(
        "--fecha",
        type=date.fromisoformat,
        default=None
    )

    parser.add_argument(
        "--continuo",
        action="store_true"
    )

    parser.add_argument(
        "--intervalo",
        type=float,
        default=10.0
    )

    parser.add_argument("--verificar-datos", action="store_true")
    parser.add_argument("--ahora", type=datetime.fromisoformat)
    parser.add_argument("--publicar-estados", action="store_true")
    parser.add_argument("--salidas", type=Path, default=Path("salidas"))
    parser.add_argument("--seguimiento-estado", action="store_true")
    parser.add_argument("--publicar-electricas", action="store_true")
    args = parser.parse_args()
    if args.seguimiento_estado and not args.verificar_datos:
        parser.error("--seguimiento-estado requiere --verificar-datos")
    if args.publicar_estados and not args.verificar_datos:
        parser.error("--publicar-estados requiere --verificar-datos")
    if args.continuo and args.ahora is not None:
        parser.error("--ahora es solo para pruebas de una ejecución")

    if args.intervalo <= 0:
        parser.error("El intervalo debe ser positivo")

    ultimo_estado_datos = None
    ultima_ruta = None
    ultima_version = None

    print(
        "Modo:",
        "continuo" if args.continuo else "una ejecución"
    )

    print("Publicación eléctrica:", "SÍ" if args.publicar_electricas else "NO")

    try:
        while True:

            dia = (
                args.fecha
                if args.fecha is not None
                else date.today()
            )

            ruta = archivo_del_dia(args.raiz, dia)

            if ruta != ultima_ruta:
                print(f"Buscando CSV del día {dia}: {ruta}")
                ultima_ruta = ruta
                ultima_version = None
                ultimo_estado_datos = None

            try:
                datos = ruta.stat()

                version = (
                    datos.st_mtime_ns,
                    datos.st_size
                )

                if version != ultima_version:

                    try:
                        inspeccionar(ruta, publicar=args.publicar_electricas)

                    except (OSError, ValueError) as error:
                        print(
                            "CSV todavía no procesable:",
                            error
                        )

                    else:
                        ultima_version = version

            except FileNotFoundError:
                print(
                    "CSV no disponible todavía:",
                    ruta
                )

            except OSError as error:
                print("Error de acceso:", error)

            # Verificar incluso cuando el CSV no cambia.
            if args.verificar_datos:
                try:
                    informe = verificar_actualizacion(
                        ruta, ahora=args.ahora
                    )
                    estado = informe["estado"]

                    # Actualizar el estado persistente en cada revisión,
                    # incluso cuando el CSV no haya cambiado.
                    if args.seguimiento_estado:
                        recuperacion = actualizar_estado(
                            informe,
                            args.salidas / "estado_datos_inversor2.json"
                        )

                        if recuperacion is not None:
                            print(
                                "RECUPERACIÓN DE DATOS DETECTADA:",
                                recuperacion["ultima_medicion"],
                                flush=True
                            )
                    if estado != ultimo_estado_datos:
                        print(f"Estado de datos: {estado} | {informe}", flush=True)
                        if args.publicar_estados and estado == "sin_actualizacion":
                            evento = crear_evento_ausencia(informe)

                            if evento is not None:
                                try:
                                    resultado = publicar_evento_unico(
                                        evento,
                                        directorio=args.salidas
                                    )

                                    print(
                                        "Evento de ausencia:",
                                        "duplicado" if resultado["duplicado"]
                                        else "nuevo"
                                    )
                                except Exception as error:
                                    print(
                                        "Error al registrar ausencia:",
                                        error
                                    )

                        ultimo_estado_datos = estado
                except (OSError, ValueError) as error:
                    print(f"No se pudo verificar la actualización: {error}")

            if not args.continuo:
                break

            time.sleep(args.intervalo)

    except KeyboardInterrupt:
        print(
            "\nSupervisión detenida por el usuario."
        )


if __name__ == "__main__":
    main()
