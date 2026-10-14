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
exec "$BROWSER" --kiosk --noerrdialogs --disable-infobars --no-first-run \
  --disable-session-crashed-bubble --password-store=basic --ozone-platform-hint=auto "$URL"
