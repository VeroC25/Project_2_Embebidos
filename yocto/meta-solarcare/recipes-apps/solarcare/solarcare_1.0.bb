SUMMARY = "Aplicaciones del sistema SolarCare AI"
DESCRIPTION = "Detector de anomalías y agente de inteligencia artificial"
LICENSE = "CLOSED"
S = "${UNPACKDIR}"

# Incorporar los archivos de configuración de los servicios.
SRC_URI = " \
    file://services/solarcare-detector.service \
    file://services/solarcare-agent.service \
"

# Habilitar la integración con systemd sin iniciar servicios todavía.
inherit systemd
SYSTEMD_SERVICE:${PN} = "solarcare-detector.service solarcare-agent.service"
SYSTEMD_AUTO_ENABLE = "disable"

# Las aplicaciones Python no requieren compilación.
do_compile() {
    :
}

# Instalar los servicios en el directorio correspondiente del sistema.
do_install() {
    install -d ${D}${systemd_system_unitdir}

    install -m 0644 ${UNPACKDIR}/services/solarcare-detector.service \
        ${D}${systemd_system_unitdir}/solarcare-detector.service

    install -m 0644 ${UNPACKDIR}/services/solarcare-agent.service \
        ${D}${systemd_system_unitdir}/solarcare-agent.service
}

# Incorporar los archivos de servicio al paquete generado.
FILES:${PN} += " \
    ${systemd_system_unitdir}/solarcare-detector.service \
    ${systemd_system_unitdir}/solarcare-agent.service \
"
