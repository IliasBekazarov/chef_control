#!/usr/bin/env bash
# ============================================================
#   Chef Control — Камера детектор баштоо
#   Иштетүү: ./run_detector.sh
#            ./run_detector.sh --source /dev/video0
#            ./run_detector.sh --no-display
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Камера колдонуучусу API маалыматтарын environment variables аркылуу өзгөртө алат
export CHEF_API_URL="${CHEF_API_URL:-http://localhost:8000/api}"
export CHEF_API_USER="${CHEF_API_USER:-admin}"
export CHEF_API_PASS="${CHEF_API_PASS:-admin123}"

# Виртуалдык чөйрө
if [ -d "$SCRIPT_DIR/venv" ]; then
    source "$SCRIPT_DIR/venv/bin/activate"
fi

cd "$SCRIPT_DIR"
echo "🎥  Детектор баштоо…"
echo "   API: $CHEF_API_URL  (колдонуучу: $CHEF_API_USER)"
echo ""
python3 main.py "$@"
