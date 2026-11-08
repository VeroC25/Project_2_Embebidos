SUMMARY = "Motor de inteligencia artificial Ollama"
DESCRIPTION = "Ollama para inferencia local mediante CPU ARM64"
LICENSE = "CLOSED"

# Utilizar los ejecutables ARM64 previamente preparados.
SRC_URI = "file://ollama-cpu file://ollama.service"
S = "${UNPACKDIR}/ollama-cpu"

# Evitar compilar o modificar los ejecutables precompilados.
do_configure[noexec] = "1"
do_compile[noexec] = "1"
INHIBIT_PACKAGE_STRIP = "1"
INHIBIT_PACKAGE_DEBUG_SPLIT = "1"
INSANE_SKIP:${PN} += "already-stripped"

# Instalar el ejecutable y conservar las bibliotecas compartidas.
do_install() {
    install -d ${D}${bindir}
    install -m 0755 ${S}/bin/ollama ${D}${bindir}/ollama

    install -d ${D}${libdir}/ollama
    cp -a ${S}/lib/ollama/. ${D}${libdir}/ollama/
}

# Incorporar las bibliotecas privadas al paquete principal.
FILES:${PN} += "${libdir}/ollama"

# Mantener juntas las bibliotecas precompiladas de Ollama.
SOLIBS = ".so"
FILES_SOLIBSDEV = ""

# Corregir los propietarios de las bibliotecas instaladas.
do_install:append() {
    chown -R 0:0 ${D}${libdir}/ollama
}

# Las bibliotecas privadas de Ollama incluyen enlaces .so usados en ejecución.
INSANE_SKIP:${PN} += "dev-so"

# Integrar Ollama con el administrador de servicios systemd.
inherit systemd

SYSTEMD_SERVICE:${PN} = "ollama.service"
SYSTEMD_AUTO_ENABLE = "enable"

# Instalar el servicio y preparar el directorio de modelos.
do_install:append() {
    install -d ${D}${systemd_system_unitdir}
    install -m 0644 ${UNPACKDIR}/ollama.service \
        ${D}${systemd_system_unitdir}/ollama.service

    install -d ${D}${localstatedir}/lib/ollama/models
}

# Incluir el servicio y el almacenamiento de modelos en el paquete.
FILES:${PN} += " \
    ${systemd_system_unitdir}/ollama.service \
    ${localstatedir}/lib/ollama \
"

# Crear una cuenta de sistema dedicada para ejecutar Ollama.
inherit useradd

USERADD_PACKAGES = "${PN}"
GROUPADD_PARAM:${PN} = "--system ollama"
USERADD_PARAM:${PN} = "--system --no-create-home --home-dir /var/lib/ollama --shell /usr/sbin/nologin --gid ollama ollama"
