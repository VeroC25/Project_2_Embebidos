SUMMARY = "Aplicaciones del sistema SolarCare AI"
DESCRIPTION = "Detector de anomalías y trabajador de inteligencia artificial"
LICENSE = "CLOSED"
S = "${UNPACKDIR}"

# Incorporar los módulos Python y las unidades de systemd.
SRC_URI = " \
    file://app/ \
    file://services/solarcare-detector.service \
    file://services/solarcare-agent.service \
    file://services/solarcare-agent.timer \
"

# Integrar los servicios sin habilitarlos automáticamente.
inherit systemd
SYSTEMD_SERVICE:${PN} = "solarcare-detector.service solarcare-agent.timer"
SYSTEMD_AUTO_ENABLE = "disable"

# Declarar las dependencias necesarias para ejecutar Python.
RDEPENDS:${PN} += "python3-core python3-modules"

# Los módulos Python no requieren compilación.
do_compile() {
    :
}

# Instalar la aplicación y sus servicios en el sistema.
do_install() {
    install -d ${D}/opt/solarcare
    install -d ${D}${localstatedir}/lib/solarcare/salidas
    ln -s ${localstatedir}/lib/solarcare/salidas ${D}/opt/solarcare/salidas
    install -d ${D}${systemd_system_unitdir}

    for archivo in ${UNPACKDIR}/app/*.py; do
        install -m 0644 "$archivo" ${D}/opt/solarcare/
    done

    install -m 0644 ${UNPACKDIR}/services/solarcare-detector.service \
        ${D}${systemd_system_unitdir}/solarcare-detector.service

    install -m 0644 ${UNPACKDIR}/services/solarcare-agent.service \
        ${D}${systemd_system_unitdir}/solarcare-agent.service

    install -m 0644 ${UNPACKDIR}/services/solarcare-agent.timer \
        ${D}${systemd_system_unitdir}/solarcare-agent.timer
}

# Incluir los módulos y servicios en el paquete generado.
FILES:${PN} += " \
    /opt/solarcare \
    ${localstatedir}/lib/solarcare/salidas \
    ${systemd_system_unitdir}/solarcare-detector.service \
    ${systemd_system_unitdir}/solarcare-agent.service \
    ${systemd_system_unitdir}/solarcare-agent.timer \
"
