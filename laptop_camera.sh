#!/usr/bin/env bash
# ============================================================
#   Chef Control — Ноутбук камерасы менен баштоо
#   ./laptop_camera.sh
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

export CHEF_API_URL="${CHEF_API_URL:-http://localhost:8000/api}"
export CHEF_API_USER="${CHEF_API_USER:-admin}"
export CHEF_API_PASS="${CHEF_API_PASS:-admin123}"

if [ -d "$SCRIPT_DIR/venv" ]; then
    source "$SCRIPT_DIR/venv/bin/activate"
fi

cd "$SCRIPT_DIR"

echo "========================================"
echo "  📷  Chef Control — Ноутбук Камерасы"
echo "========================================"
echo ""
echo "  Камера   : /dev/video0 (индекс 0)"
echo "  API      : $CHEF_API_URL"
echo "  Монитор  : http://localhost:5173/monitor"
echo ""
echo "  Токтотуу : Ctrl+C"
echo "========================================"
echo ""

# GUI терезеси: Mac'та OpenCV терезеси үчүн --no-display
# Эгер терезе ачкыңыз келсе, --no-display жок кылыңыз
python3 main.py --source 0 --interval 10 --no-display
