#!/usr/bin/env bash
# Runs on the Pi from the app directory (called by `make deploy`). Safe to re-run.
set -euo pipefail

APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
APP_USER="$(id -un)"
cd "$APP_DIR"

echo ">> Python dependencies"
[ -d venv ] || python3 -m venv venv
venv/bin/pip install --quiet --upgrade pip
venv/bin/pip install --quiet -r requirements.txt

echo ">> systemd service"
# Replace the old per-user template unit if it was ever installed.
if [ -f /etc/systemd/system/billboard@.service ]; then
  sudo systemctl disable --now "billboard@${APP_USER}.service" || true
  sudo rm -f /etc/systemd/system/billboard@.service
fi
sed -e "s|__USER__|${APP_USER}|g" -e "s|__APP_DIR__|${APP_DIR}|g" deploy/billboard.service \
  | sudo tee /etc/systemd/system/billboard.service > /dev/null
sudo systemctl daemon-reload
sudo systemctl enable billboard.service
sudo systemctl restart billboard.service

echo ">> Kiosk autostart"
chmod +x deploy/kiosk.sh
mkdir -p ~/.config/autostart
cat > ~/.config/autostart/billboard-kiosk.desktop <<DESKTOP
[Desktop Entry]
Type=Application
Name=Billboard Kiosk
Exec=${APP_DIR}/deploy/kiosk.sh
X-GNOME-Autostart-enabled=true
DESKTOP

if command -v raspi-config > /dev/null; then
  echo ">> Desktop auto-login + screen blanking off"
  sudo raspi-config nonint do_boot_behaviour B4
  sudo raspi-config nonint do_blanking 1
fi

echo ">> Done. Service status:"
systemctl --no-pager --lines=0 status billboard.service || true
