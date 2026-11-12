#!/usr/bin/env bash
# Instala el código y servicios respaldados en una Raspberry Pi accesible por SSH.
# No instala dependencias, no descarga modelos y NO configura acceso al SESLAB.
set -euo pipefail
if [[ $# -ne 1 ]]; then
  echo "Uso: $0 root@IP_DE_LA_RASPBERRY" >&2
  exit 2
fi
TARGET="$1"
BASE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE="$BASE/yocto/meta-solarcare/recipes-apps/solarcare/files"
ssh "$TARGET" 'mkdir -p /opt/solarcare /usr/lib/systemd/system /etc/systemd/system/solarcare-web.service.d /var/lib/solarcare/salidas'
tar -C "$SOURCE/solarcare" -cf - . | ssh "$TARGET" 'tar -C /opt/solarcare -xf -'
for name in solarcare-detector.service solarcare-agent.service solarcare-agent.timer solarcare-web.service; do
  scp "$SOURCE/services/$name" "$TARGET:/usr/lib/systemd/system/$name"
done
scp "$SOURCE/services/solarcare-web-override.conf" "$TARGET:/etc/systemd/system/solarcare-web.service.d/override.conf"
ssh "$TARGET" 'systemctl daemon-reload; python3 -c "import flask, ollama" || true; echo "Archivos instalados. Configurá CSV, dependencias y modelos antes de habilitar servicios."'
echo 'Revisá docs/instalacion-otra-raspberry.md para continuar.'
