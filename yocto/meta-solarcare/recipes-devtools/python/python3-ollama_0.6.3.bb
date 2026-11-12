SUMMARY = "Cliente Python oficial de Ollama"
DESCRIPTION = "Cliente Python para comunicarse con el servidor Ollama"
HOMEPAGE = "https://github.com/ollama/ollama-python"

LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://LICENSE;md5=a8abe7311c869aba169d640cf367a4af"

SRC_URI[sha256sum] = "41fc49a8095c4a75939c4c1f8582e4d0671692fb6eac2a5a7ede8c9872b67096"

inherit pypi python_hatchling

DEPENDS += "python3-hatch-vcs-native"

# Proporcionar la versión del paquete sin depender del historial Git.
export SETUPTOOLS_SCM_PRETEND_VERSION = "${PV}"

# Instalar las dependencias necesarias para el cliente Python.
RDEPENDS:${PN} += " \
    python3-httpx \
    python3-pydantic \
"
