SUMMARY = "Aplicaciones y servicios del sistema SolarCare AI"
DESCRIPTION = "Detector de anomalías, agente de IA y dashboard Flask"
LICENSE = "CLOSED"
S = "${UNPACKDIR}"

# Código respaldado de la Raspberry Pi el 12/11/2026.
# Las dependencias Python externas (Flask y ollama) deben resolverse
# en la imagen: ver docs/instalacion-otra-raspberry.md.
SRC_URI = " \
    file://solarcare/agente_solarcare.py \
    file://solarcare/detectar_ausencia_datos.py \
    file://solarcare/detector_solarcare.py \
    file://solarcare/eventos_ausencia_solarcare.py \
    file://solarcare/monitor_diario_solarcare.py \
    file://solarcare/monitorear_csv_solarcare.py \
    file://solarcare/publicacion_unica.py \
    file://solarcare/puente_detector_ia.py \
    file://solarcare/seguimiento_estado_datos.py \
    file://solarcare/trabajador_ia.py \
    file://solarcare/web/app.py \
    file://solarcare/web/static/app.js \
    file://solarcare/web/static/styles.css \
    file://solarcare/web/templates/index.html \
    file://services/solarcare-detector.service \
    file://services/solarcare-agent.service \
    file://services/solarcare-agent.timer \
    file://services/solarcare-web.service \
    file://services/solarcare-web-override.conf \
"

inherit systemd
SYSTEMD_SERVICE:${PN} = "solarcare-detector.service solarcare-agent.service solarcare-agent.timer solarcare-web.service"
# No iniciar automáticamente hasta configurar el origen CSV y los modelos.
SYSTEMD_AUTO_ENABLE = "disable"

do_compile() {
    :
}

do_install() {
    install -d ${D}/opt/solarcare/web/templates
    install -d ${D}/opt/solarcare/web/static
    install -d ${D}${systemd_system_unitdir}
    install -d ${D}${sysconfdir}/systemd/system/solarcare-web.service.d
    install -d ${D}${localstatedir}/lib/solarcare/salidas

    install -m 0644 ${UNPACKDIR}/solarcare/agente_solarcare.py ${D}/opt/solarcare/agente_solarcare.py
    install -m 0644 ${UNPACKDIR}/solarcare/detectar_ausencia_datos.py ${D}/opt/solarcare/detectar_ausencia_datos.py
    install -m 0644 ${UNPACKDIR}/solarcare/detector_solarcare.py ${D}/opt/solarcare/detector_solarcare.py
    install -m 0644 ${UNPACKDIR}/solarcare/eventos_ausencia_solarcare.py ${D}/opt/solarcare/eventos_ausencia_solarcare.py
    install -m 0644 ${UNPACKDIR}/solarcare/monitor_diario_solarcare.py ${D}/opt/solarcare/monitor_diario_solarcare.py
    install -m 0644 ${UNPACKDIR}/solarcare/monitorear_csv_solarcare.py ${D}/opt/solarcare/monitorear_csv_solarcare.py
    install -m 0644 ${UNPACKDIR}/solarcare/publicacion_unica.py ${D}/opt/solarcare/publicacion_unica.py
    install -m 0644 ${UNPACKDIR}/solarcare/puente_detector_ia.py ${D}/opt/solarcare/puente_detector_ia.py
    install -m 0644 ${UNPACKDIR}/solarcare/seguimiento_estado_datos.py ${D}/opt/solarcare/seguimiento_estado_datos.py
    install -m 0644 ${UNPACKDIR}/solarcare/trabajador_ia.py ${D}/opt/solarcare/trabajador_ia.py
    install -m 0644 ${UNPACKDIR}/solarcare/web/app.py ${D}/opt/solarcare/web/app.py
    install -m 0644 ${UNPACKDIR}/solarcare/web/static/app.js ${D}/opt/solarcare/web/static/app.js
    install -m 0644 ${UNPACKDIR}/solarcare/web/static/styles.css ${D}/opt/solarcare/web/static/styles.css
    install -m 0644 ${UNPACKDIR}/solarcare/web/templates/index.html ${D}/opt/solarcare/web/templates/index.html

    install -m 0644 ${UNPACKDIR}/services/solarcare-detector.service ${D}${systemd_system_unitdir}/solarcare-detector.service
    install -m 0644 ${UNPACKDIR}/services/solarcare-agent.service ${D}${systemd_system_unitdir}/solarcare-agent.service
    install -m 0644 ${UNPACKDIR}/services/solarcare-agent.timer ${D}${systemd_system_unitdir}/solarcare-agent.timer
    install -m 0644 ${UNPACKDIR}/services/solarcare-web.service ${D}${systemd_system_unitdir}/solarcare-web.service

    install -m 0644 ${UNPACKDIR}/services/solarcare-web-override.conf \
        ${D}${sysconfdir}/systemd/system/solarcare-web.service.d/override.conf
    ln -s /var/lib/solarcare/salidas ${D}/opt/solarcare/salidas
}

FILES:${PN} += " \
    /opt/solarcare \
    ${systemd_system_unitdir}/solarcare-detector.service \
    ${systemd_system_unitdir}/solarcare-agent.service \
    ${systemd_system_unitdir}/solarcare-agent.timer \
    ${systemd_system_unitdir}/solarcare-web.service \
    ${sysconfdir}/systemd/system/solarcare-web.service.d/override.conf \
    ${localstatedir}/lib/solarcare \
"

RDEPENDS:${PN} += "python3-core python3-modules"
