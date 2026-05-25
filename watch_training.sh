#!/bin/bash
# Окутуу прогрессин карап туруу скрипти
LOG="runs/detect/chef_detector/train_log.txt"
echo "📊  Окутуу прогресси (жаңыртылат...)"
echo "    Чыгуу үчүн → Ctrl+C"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
tail -f "$LOG" | grep -E "(Epoch|all |mAP|best|Finished|Results)"
