"""
Telegram алерт сервиси — Telegram Bot API аркылуу бузуу жөнүндө билдируу жиберет.
"""
import requests
from django.utils import timezone
from datetime import timedelta


TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"


def send_alert(record) -> bool:
    """
    DetectionRecord бузуу болгондо Telegram'га алерт жиберет.
    Cooldown жана threshold текшерилет.
    True — жиберилди, False — жиберилген жок.
    """
    from .models import AlertSettings

    cfg = AlertSettings.get()

    if not cfg.enabled or not cfg.bot_token or not cfg.chat_id:
        return False

    # Катары бузуулар санагычын жаңылоо
    if record.is_compliant:
        cfg.consecutive_violations = 0
        cfg.save(update_fields=["consecutive_violations"])
        return False

    cfg.consecutive_violations += 1

    # Threshold текшерүү
    if cfg.consecutive_violations < cfg.violation_threshold:
        cfg.save(update_fields=["consecutive_violations"])
        return False

    # Cooldown текшерүү
    if cfg.last_alert_at:
        next_allowed = cfg.last_alert_at + timedelta(minutes=cfg.cooldown_minutes)
        if timezone.now() < next_allowed:
            cfg.save(update_fields=["consecutive_violations"])
            return False

    # Алерт жазуу
    violations_text = "\n".join(
        f"  • {v}" for v in record.violations_list()
    ) or "  • Белгисиз бузуу"

    ts = record.timestamp.strftime("%d.%m.%Y %H:%M:%S") if record.timestamp else "—"

    text = (
        "🚨 *Chef Control — Шарт бузулду!*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"🕐 *Убакыт:* `{ts}`\n"
        f"👤 *Адамдар:* `{record.person_count}`\n"
        f"🎩 *Шляпа:* {'✅' if record.has_hat else '❌'} `({record.hat_confidence:.0%})`\n"
        f"👔 *Фартук:* {'✅' if record.has_apron else '❌'} `({record.apron_confidence:.0%})`\n"
        f"⚠️ *Бузуулар:*\n{violations_text}\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"📊 Катары бузуулар: `{cfg.consecutive_violations}`"
    )

    ok = _send_message(cfg.bot_token, cfg.chat_id, text)

    if ok:
        cfg.last_alert_at = timezone.now()
        cfg.consecutive_violations = 0

    cfg.save(update_fields=["last_alert_at", "consecutive_violations"])
    return ok


def send_test_message(bot_token: str, chat_id: str) -> tuple[bool, str]:
    """
    Тест алерт жиберет — Settings бетинен чакырылат.
    (ok, error_message) кайтарат.
    """
    text = (
        "✅ *Chef Control — Тест алерт*\n"
        "Telegram интеграциясы туура иштеп жатат!"
    )
    try:
        ok = _send_message(bot_token, chat_id, text)
        return (True, "") if ok else (False, "Telegram API ката кайтарды")
    except Exception as e:
        return False, str(e)


def _send_message(token: str, chat_id: str, text: str) -> bool:
    url = TELEGRAM_API.format(token=token)
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
    }
    try:
        resp = requests.post(url, json=payload, timeout=8)
        return resp.status_code == 200 and resp.json().get("ok", False)
    except requests.RequestException:
        return False
