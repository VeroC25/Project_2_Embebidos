#!/bin/sh

# Detener el procedimiento ante errores.
set -eu

DISCO="/dev/mmcblk0"
PARTICION="/dev/mmcblk0p2"

# Comprobar que estamos trabajando con la partición raíz esperada.
if [ ! -b "$DISCO" ] || [ ! -b "$PARTICION" ]; then
    echo "SolarCare: no se encontró la microSD esperada."
    exit 1
fi

RAIZ_DISPOSITIVO=$(findmnt -n -o MAJ:MIN /)
PARTICION_DISPOSITIVO=$(cat /sys/class/block/mmcblk0p2/dev)

if [ "$RAIZ_DISPOSITIVO" != "$PARTICION_DISPOSITIVO" ]; then
    echo "SolarCare: dispositivo raíz inesperado."
    exit 1
fi

# Consultar el espacio disponible en el dispositivo.
SECTORES_PARTICION=$(cat /sys/class/block/mmcblk0p2/size)
SECTOR_INICIAL=$(cat /sys/class/block/mmcblk0p2/start)
SECTORES_DISCO=$(cat /sys/class/block/mmcblk0/size)

FINAL_ACTUAL=$((SECTOR_INICIAL + SECTORES_PARTICION - 1))
FINAL_DISCO=$((SECTORES_DISCO - 1))

# Consultar el último sector registrado en la tabla de particiones.
FINAL_TABLA=$(parted -m "$DISCO" unit s print |
    awk -F: '$1 == "2" {gsub(/s/, "", $3); print $3}')

# Verificar que la tabla conserva el sector inicial de la partición.
INICIO_TABLA=$(parted -m "$DISCO" unit s print |
    awk -F: '$1 == "2" {gsub(/s/, "", $2); print $2}')

if [ -z "$INICIO_TABLA" ] || [ "$INICIO_TABLA" != "$SECTOR_INICIAL" ]; then
    echo "SolarCare: el sector inicial no coincide con el kernel."
    exit 1
fi

# Detener el procedimiento si no se pudo identificar la partición.
if [ -z "$FINAL_TABLA" ]; then
    echo "SolarCare: no se pudo consultar la tabla de particiones."
    exit 1
fi


# Ampliar la partición solamente si la tabla todavía tiene espacio libre.
if [ "$FINAL_TABLA" -lt "$((FINAL_DISCO - 2048))" ]; then
    echo "SolarCare: ampliando la partición raíz."
    parted -s "$DISCO" resizepart 2 100%

    # Comprobar que la tabla registra una partición más grande.
    NUEVO_FINAL=$(parted -m "$DISCO" unit s print |
        awk -F: '$1 == "2" {gsub(/s/, "", $3); print $3}')

    if [ -z "$NUEVO_FINAL" ] || [ "$NUEVO_FINAL" -le "$FINAL_TABLA" ]; then
        echo "SolarCare: no se pudo confirmar la ampliación."
        exit 1
    fi

    echo "SolarCare: se requiere reiniciar para continuar."
    exit 0
fi

# Evitar ampliar EXT4 si el kernel y la tabla no coinciden.
if [ "$FINAL_ACTUAL" -ne "$FINAL_TABLA" ]; then
    echo "SolarCare: el kernel y la tabla de particiones no coinciden."
    echo "SolarCare: se requiere revisar el estado o reiniciar."
    exit 1
fi

# Ampliar EXT4 cuando el kernel ya reconoce la partición completa.
echo "SolarCare: comprobando el tamaño de EXT4."
resize2fs "$PARTICION"

echo "SolarCare: almacenamiento preparado."
