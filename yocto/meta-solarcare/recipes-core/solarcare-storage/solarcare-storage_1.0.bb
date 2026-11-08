SUMMARY = "Gestion del almacenamiento de SolarCare AI"
DESCRIPTION = "Herramientas para ampliar la particion raiz en Raspberry Pi"
LICENSE = "CLOSED"

SRC_URI = " \
    file://solarcare-expand-rootfs.sh \
    file://solarcare-expand-rootfs.service \
"

S = "${UNPACKDIR}"

# Integrar el servicio con systemd sin habilitarlo automáticamente.
inherit systemd

SYSTEMD_SERVICE:${PN} = "solarcare-expand-rootfs.service"
SYSTEMD_AUTO_ENABLE = "disable"

# Instalar el script y la unidad de servicio en sus rutas definitivas.
do_install() {
    install -d ${D}${sbindir}
    install -m 0755 ${UNPACKDIR}/solarcare-expand-rootfs.sh \
        ${D}${sbindir}/solarcare-expand-rootfs.sh

    install -d ${D}${systemd_system_unitdir}
    install -m 0644 ${UNPACKDIR}/solarcare-expand-rootfs.service \
        ${D}${systemd_system_unitdir}/solarcare-expand-rootfs.service
}

# Incluir ambos archivos en el paquete generado.
FILES:${PN} += " \
    ${sbindir}/solarcare-expand-rootfs.sh \
    ${systemd_system_unitdir}/solarcare-expand-rootfs.service \
"
