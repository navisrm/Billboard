#!/usr/bin/env bash
# Opens the billboard full screen once the server is up. Started at desktop login
# via ~/.config/autostart/billboard-kiosk.desktop (installed by deploy/install.sh).
APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PORT="$(grep -E '^PORT=' "$APP_DIR/.env" 2>/dev/null | cut -d= -f2)"
URL="http://localhost:${PORT:-8000}"

until curl -fs -o /dev/null "$URL"; do
  sleep 2
done

BROWSER="$(command -v chromium || command -v chromium-browser)"

# Raspberry Pi OS uses Wayland (labwc). Newer Chromium falls back to X11 with
# --ozone-platform-hint=auto, which gives a blank screen or no window, so select the platform.
if [ -n "${WAYLAND_DISPLAY:-}" ]; then
  PLATFORM=wayland
else
  PLATFORM=x11
fi

# Start the browser again if it crashes or closes, so the screen does not stay blank.
while true; do
  "$BROWSER" --kiosk --noerrdialogs --disable-infobars --no-first-run \
    --disable-session-crashed-bubble --password-store=basic --ozone-platform="$PLATFORM" "$URL"
  sleep 5
done
