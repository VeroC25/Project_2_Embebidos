from datetime import date as FechaReal
from pathlib import Path
from unittest.mock import patch

import monitor_diario_solarcare as monitor


def test_cambio_automatico_de_dia(tmp_path):
    raiz = tmp_path / "Inversor 2"

    fechas = [
        FechaReal(2026, 11, 1),
        FechaReal(2026, 11, 2),
    ]

    # Crear dos archivos ficticios en carpetas diarias.
    for dia in fechas:
        ruta = monitor.archivo_del_dia(raiz, dia)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(
            "archivo de prueba",
            encoding="utf-8"
        )

    # Simular el cambio de fecha.
    class RelojSimulado:
        dia_actual = fechas[0]
        fromisoformat = staticmethod(
            FechaReal.fromisoformat
        )

        @classmethod
        def today(cls):
            return cls.dia_actual

    analizados = []

    def inspeccion_falsa(ruta, publicar=False):
        assert publicar is False
        analizados.append(Path(ruta))

    def avanzar_tiempo(_segundos):
        if len(analizados) == 1:
            RelojSimulado.dia_actual = fechas[1]
        elif len(analizados) >= 2:
            raise KeyboardInterrupt

    with (
        patch.object(monitor, "date", RelojSimulado),
        patch.object(
            monitor,
            "inspeccionar",
            side_effect=inspeccion_falsa
        ),
        patch.object(
            monitor.time,
            "sleep",
            side_effect=avanzar_tiempo
        ),
        patch(
            "sys.argv",
            [
                "monitor_diario_solarcare.py",
                "--raiz",
                str(raiz),
                "--continuo",
            ]
        ),
    ):
        monitor.main()

    assert analizados == [
        monitor.archivo_del_dia(raiz, fechas[0]),
        monitor.archivo_del_dia(raiz, fechas[1]),
    ]
