#!/usr/bin/env bash
# ============================================================
#   Chef Control — Баарын баштоо скрипти
#   Иштетүү: ./start.sh
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"
LOG_DIR="$SCRIPT_DIR/logs"

mkdir -p "$LOG_DIR"

echo "========================================"
echo "  🍳  Chef Control — Баштоо"
echo "========================================"

# ─── Backend (Django) ────────────────────────────────────────
echo ""
echo "▶ Django backend баштоо (port 8000)…"

# Виртуалдык чөйрө бар болсо иштет
if [ -d "$SCRIPT_DIR/venv" ]; then
    source "$SCRIPT_DIR/venv/bin/activate"
fi

cd "$BACKEND_DIR"
python3 manage.py migrate --run-syncdb > "$LOG_DIR/django.log" 2>&1 || true
nohup python3 manage.py runserver 0.0.0.0:8000 >> "$LOG_DIR/django.log" 2>&1 &
DJANGO_PID=$!
echo "  Django PID: $DJANGO_PID"
echo $DJANGO_PID > "$LOG_DIR/django.pid"

# ─── Frontend (React/Vite) ───────────────────────────────────
echo ""
echo "▶ React frontend баштоо (port 5173)…"
cd "$FRONTEND_DIR"

# node_modules жок болсо орнот
if [ ! -d "node_modules" ]; then
    echo "  npm install иштеп жатат…"
    npm install --legacy-peer-deps
fi

nohup npx vite --host 0.0.0.0 >> "$LOG_DIR/frontend.log" 2>&1 &
VITE_PID=$!
echo "  Vite PID: $VITE_PID"
echo $VITE_PID > "$LOG_DIR/frontend.pid"

# ─── Жыйынтык ───────────────────────────────────────────────
sleep 2
echo ""
echo "========================================"
echo "  ✅  Баары иштеп жатат!"
echo ""
echo "  🌐  Web:     http://localhost:5173"
echo "  🔌  API:     http://localhost:8000/api"
echo "  👤  Admin:   admin / admin123"
echo ""
echo "  📷  Детектор баштоо:"
echo "      cd $SCRIPT_DIR"
echo "      python3 main.py --source 0"
echo ""
echo "  ⛔  Токтотуу:"
echo "      ./stop.sh"
echo "========================================"
