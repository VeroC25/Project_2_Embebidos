SUMMARY = "Imagen Linux para SolarCare AI"
DESCRIPTION = "Sistema embebido para monitoreo fotovoltaico en Raspberry Pi 4"
LICENSE = "MIT"

# Utilizar la imagen base de Yocto como punto de partida
require recipes-core/images/core-image-base.bb

# Incorporar Python y herramientas necesarias para el sistema
IMAGE_INSTALL:append = " \
    python3 \
    python3-core \
    python3-modules \
    openssh \
    solarcare \
    ollama \
    python3-ollama \
    solarcare-storage \
    cifs-utils \
    parted \
    e2fsprogs-resize2fs \
    util-linux-findmnt \
"

# Reservar espacio adicional para archivos y registros
IMAGE_ROOTFS_EXTRA_SPACE = "1048576"
