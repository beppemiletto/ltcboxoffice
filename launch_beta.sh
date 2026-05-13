#!/bin/bash
# Launch script for LTC BoxOffice beta server
# Usage: ./launch_beta.sh [--port PORT] [--workers N]

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$PROJECT_DIR/.env"
ENV_FILE="$PROJECT_DIR/.env.beta"
SETTINGS="ltcboxoffice.settings.beta"
PORT="${2:-8000}"
WORKERS="${4:-3}"

# Parse named args
while [[ $# -gt 0 ]]; do
    case $1 in
        --port) PORT="$2"; shift 2 ;;
        --workers) WORKERS="$2"; shift 2 ;;
        *) shift ;;
    esac
done

echo "========================================="
echo "  LTC BoxOffice - Beta Server"
echo "========================================="

# Check virtualenv
if [ ! -f "$VENV/bin/activate" ]; then
    echo "[ERROR] Virtualenv non trovato in $VENV"
    exit 1
fi

# Check .env.beta
if [ ! -f "$ENV_FILE" ]; then
    echo "[ERROR] File $ENV_FILE non trovato"
    exit 1
fi

# Activate virtualenv
echo "[1/4] Attivazione virtualenv..."
source "$VENV/bin/activate"

# Load environment variables
echo "[2/4] Caricamento variabili d'ambiente da .env.beta..."
export $(grep -v '^#' "$ENV_FILE" | xargs)
export DJANGO_SETTINGS_MODULE="$SETTINGS"

# Kill any existing gunicorn on that port
EXISTING=$(lsof -i :$PORT -t 2>/dev/null || true)
if [ -n "$EXISTING" ]; then
    echo "      Fermo processo esistente sulla porta $PORT (PID $EXISTING)..."
    kill -9 $EXISTING 2>/dev/null || true
    sleep 1
fi

# Collectstatic
echo "[3/4] Collectstatic..."
python manage.py collectstatic --noinput -v 0

# Launch gunicorn
echo "[4/4] Avvio Gunicorn su 0.0.0.0:$PORT con $WORKERS worker..."
echo "-----------------------------------------"
echo "  URL locale:  http://127.0.0.1:$PORT"
echo "  URL LAN:     http://$(hostname -I | awk '{print $1}'):$PORT"
echo "  ALLOWED_HOSTS: $ALLOWED_HOSTS"
echo "-----------------------------------------"
echo "  Premi CTRL+C per fermare il server"
echo "========================================="

exec gunicorn ltcboxoffice.wsgi:application \
    --bind "0.0.0.0:$PORT" \
    --workers "$WORKERS" \
    --reload \
    --access-logfile - \
    --error-logfile -
