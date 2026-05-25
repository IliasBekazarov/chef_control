#!/usr/bin/env bash
# ============================================================
#   Chef Control — Баарын токтотуу скрипти
#   Иштетүү: ./stop.sh
# ============================================================

LOG_DIR="$(cd "$(dirname "$0")" && pwd)/logs"

echo "⛔  Chef Control токтоп жатат…"

stop_pid() {
    local name="$1"
    local pidfile="$LOG_DIR/$2"
    if [ -f "$pidfile" ]; then
        PID=$(cat "$pidfile")
        if kill -0 "$PID" 2>/dev/null; then
            kill "$PID" && echo "  ✓ $name токтотулду (PID $PID)"
        fi
        rm -f "$pidfile"
    fi
}

stop_pid "Django"   "django.pid"
stop_pid "Frontend" "frontend.pid"

# Fallback: процесс аты менен
pkill -f "manage.py runserver" 2>/dev/null && echo "  ✓ Django (pkill)" || true
pkill -f "vite"                2>/dev/null && echo "  ✓ Vite (pkill)"   || true

echo ""
echo "✅  Баары токтотулду."
