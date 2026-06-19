#!/usr/bin/env bash
# ============================================================
#   Chef Control — Production баштоо скрипти
#   Иштетүү: ./start.sh
#   Токтотуу: Ctrl+C
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
LOG_DIR="$SCRIPT_DIR/logs"
NGROK_DOMAIN="moisture-fancy-outright.ngrok-free.dev"

mkdir -p "$LOG_DIR"

echo "========================================================"
echo "  Chef Control — Production Mode"
echo "========================================================"

# Эски процесстерди токтот
pkill -f "manage.py runserver" 2>/dev/null || true
pkill -f "ngrok http"          2>/dev/null || true
sleep 1

# ─── Backend (Django ASGI + WebSocket) ───────────────────────
echo ""
echo "  Django backend баштоо (port 8000)..."
cd "$BACKEND_DIR"
python3 manage.py migrate --noinput > "$LOG_DIR/django.log" 2>&1 || true
python3 manage.py runserver 0.0.0.0:8000 >> "$LOG_DIR/django.log" 2>&1 &
DJANGO_PID=$!
echo "  PID: $DJANGO_PID  |  Log: $LOG_DIR/django.log"

# Django даяр болгончо күт
for i in {1..10}; do
    sleep 1
    curl -s http://localhost:8000/api/ > /dev/null 2>&1 && break
done
echo "  Django даяр"

# ─── ngrok Tunnel (туруктуу domain) ──────────────────────────
echo ""
echo "  ngrok tunnel баштоо ($NGROK_DOMAIN)..."
ngrok http 8000 \
    --domain="$NGROK_DOMAIN" \
    --log=stdout \
    --log-format=json > "$LOG_DIR/ngrok.log" 2>&1 &
NGROK_PID=$!
sleep 4
echo "  PID: $NGROK_PID  |  Log: $LOG_DIR/ngrok.log"

# ─── Жыйынтык ────────────────────────────────────────────────
echo ""
echo "========================================================"
echo "  Колдонуучулар үчүн:"
echo "    https://chef-control-eight.vercel.app"
echo ""
echo "  Backend (API + WebSocket):"
echo "    https://$NGROK_DOMAIN"
echo ""
echo "  Камераны баштоо үчүн (башка терминалда):"
echo "    cd $SCRIPT_DIR && python3 main.py"
echo ""
echo "  Токтотуу: Ctrl+C"
echo "========================================================"

# Ctrl+C менен бардыгын токтот
cleanup() {
    echo ""
    echo "  Токтотулуп жатат..."
    kill $DJANGO_PID $NGROK_PID 2>/dev/null || true
    pkill -f "manage.py runserver" 2>/dev/null || true
    pkill -f "ngrok http"          2>/dev/null || true
    echo "  Бардыгы токтоду."
    exit 0
}
trap cleanup INT TERM

wait $DJANGO_PID
