SUMMARY = "Aplicaciones del sistema SolarCare AI"
DESCRIPTION = "Detector de anomalías, trabajador de IA e interfaz web Flask"
LICENSE = "CLOSED"
S = "${UNPACKDIR}"

# Incorporar los módulos Python, la interfaz web y los servicios systemd.
SRC_URI = " \
    file://app/ \
    file://web/ \
    file://services/solarcare-detector.service \
    file://services/solarcare-agent.service \
    file://services/solarcare-agent.timer \
    file://services/solarcare-web.service \
"

# Registrar los servicios sin habilitarlos automáticamente.
inherit systemd

SYSTEMD_SERVICE:${PN} = " \
    solarcare-detector.service \
    solarcare-agent.service \
    solarcare-agent.timer \
    solarcare-web.service \
"

SYSTEMD_AUTO_ENABLE = "enable"

# Incorporar las dependencias de Python, Ollama y Flask.
RDEPENDS:${PN} += " \
    python3-core \
    python3-modules \
    python3-ollama \
    python3-flask \
"

# Los módulos Python no requieren compilación.
do_compile() {
    :
}

# Instalar el detector, el trabajador de IA y la interfaz web.
do_install() {
    install -d ${D}/opt/solarcare
    install -d ${D}/opt/solarcare/web/static
    install -d ${D}/opt/solarcare/web/templates
    install -d ${D}${localstatedir}/lib/solarcare/salidas
    install -d ${D}${systemd_system_unitdir}

    # Mantener las salidas del detector en un directorio persistente.
    ln -s ${localstatedir}/lib/solarcare/salidas \
        ${D}/opt/solarcare/salidas

    # Instalar los módulos principales de SolarCare.
    for archivo in ${UNPACKDIR}/app/*.py; do
        install -m 0644 "$archivo" ${D}/opt/solarcare/
    done

    # Instalar Flask y sus recursos HTML, CSS y JavaScript.
    install -m 0644 ${UNPACKDIR}/web/app.py \
        ${D}/opt/solarcare/web/app.py

    install -m 0644 ${UNPACKDIR}/web/static/* \
        ${D}/opt/solarcare/web/static/

    install -m 0644 ${UNPACKDIR}/web/templates/* \
        ${D}/opt/solarcare/web/templates/

    # Instalar los servicios del detector y del trabajador de IA.
    install -m 0644 ${UNPACKDIR}/services/solarcare-detector.service \
        ${D}${systemd_system_unitdir}/solarcare-detector.service

    install -m 0644 ${UNPACKDIR}/services/solarcare-agent.service \
        ${D}${systemd_system_unitdir}/solarcare-agent.service

    install -m 0644 ${UNPACKDIR}/services/solarcare-agent.timer \
        ${D}${systemd_system_unitdir}/solarcare-agent.timer

    # Instalar el servicio independiente de la interfaz web.
    install -m 0644 ${UNPACKDIR}/services/solarcare-web.service \
        ${D}${systemd_system_unitdir}/solarcare-web.service
}

# Incorporar todos los archivos de SolarCare al paquete.
FILES:${PN} += " \
    /opt/solarcare \
    ${localstatedir}/lib/solarcare/salidas \
    ${systemd_system_unitdir}/solarcare-detector.service \
    ${systemd_system_unitdir}/solarcare-agent.service \
    ${systemd_system_unitdir}/solarcare-agent.timer \
    ${systemd_system_unitdir}/solarcare-web.service \
"
