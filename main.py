"""
Chef Control in Kitchen — Башкы скрипт
=======================================
Иштетүү:  python main.py
           python main.py --source video.mp4
           python main.py --source 0 --no-display
           python main.py --no-api          # API жок, CSV гана
"""

import argparse
import time
import signal
import sys
import os
import tempfile
from datetime import datetime

import cv2
import requests

import config
from detector import ChefComplianceDetector
from report_manager import ReportManager


# ─── Signal handler (Ctrl+C менен чыкканда жыйынтык чыгарсын) ───────────────
_running = True

def _handle_signal(sig, frame_):
    global _running
    print("\n[ChefControl] Токтотулуп жатат…")
    _running = False

signal.signal(signal.SIGINT,  _handle_signal)
signal.signal(signal.SIGTERM, _handle_signal)


# ─── API Ingest ───────────────────────────────────────────────────────────────
API_BASE    = os.environ.get("CHEF_API_URL",  "http://localhost:8000/api")
API_USER    = os.environ.get("CHEF_API_USER", "admin")
API_PASS    = os.environ.get("CHEF_API_PASS", "admin123")

_api_token    = None
_api_session_id = None


def _api_login() -> bool:
    """JWT token алат."""
    global _api_token
    try:
        r = requests.post(f"{API_BASE}/auth/login/",
                          json={"username": API_USER, "password": API_PASS},
                          timeout=5)
        if r.status_code == 200:
            _api_token = r.json()["access"]
            print(f"[API] Кирдик: {API_USER}")
            return True
        else:
            print(f"[API] Кирүү катасы: {r.status_code}")
    except Exception as e:
        print(f"[API] Туташа алган жок: {e}")
    return False


def _ensure_api_session(session_id: str) -> bool:
    """DetectionSession жараткан/текшерет."""
    global _api_session_id
    if _api_session_id == session_id:
        return True
    try:
        headers = {"Authorization": f"Bearer {_api_token}"}
        r = requests.post(f"{API_BASE}/sessions/",
                          json={"session_id": session_id, "notes": "auto-created by detector"},
                          headers=headers, timeout=5)
        if r.status_code in (200, 201):
            _api_session_id = session_id
            return True
        elif r.status_code == 400 and "unique" in r.text.lower():
            # Already exists
            _api_session_id = session_id
            return True
    except Exception as e:
        print(f"[API] Сессия катасы: {e}")
    return False


def ingest_to_api(det, frame, session_id: str):
    """Текшерүү жыйынтыгын веб APIга жөнөтөт.
    det — DetectionResult dataclass же dict болушу мүмкүн.
    """
    global _api_token
    if not _api_token:
        if not _api_login():
            return
    _ensure_api_session(session_id)

    # DetectionResult → dict
    if hasattr(det, "__dataclass_fields__"):
        viol_str = "|".join(det.violations) if det.violations else ""
        d = {
            "is_compliant":     det.is_compliant,
            "has_hat":          det.has_hat,
            "hat_confidence":   det.hat_confidence,
            "has_apron":        det.has_apron,
            "apron_confidence": det.apron_confidence,
            "person_count":     det.person_count,
            "violations":       viol_str,
        }
    else:
        viol = det.get("violations", "")
        if isinstance(viol, list):
            viol = "|".join(viol)
        d = {
            "is_compliant":     det.get("is_compliant", False),
            "has_hat":          det.get("has_hat", False),
            "hat_confidence":   det.get("hat_confidence", 0.0),
            "has_apron":        det.get("has_apron", False),
            "apron_confidence": det.get("apron_confidence", 0.0),
            "person_count":     det.get("person_count", 0),
            "violations":       viol,
        }

    ts = datetime.now().isoformat()

    # Violation болсо кадрды сактоо
    files = {}
    tmpf  = None
    if not d["is_compliant"] and frame is not None:
        try:
            tmpf = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
            cv2.imwrite(tmpf.name, frame)
            tmpf.close()
            files = {"frame_image": ("frame.jpg", open(tmpf.name, "rb"), "image/jpeg")}
        except Exception as e:
            print(f"[API] Кадр сактоо катасы: {e}")

    try:
        headers = {"Authorization": f"Bearer {_api_token}"}

        # Session pk табуу
        session_pk = None
        resp = requests.get(f"{API_BASE}/sessions/",
                            params={"session_id": session_id},
                            headers=headers, timeout=5)
        if resp.status_code == 200:
            items = resp.json().get("results") or resp.json()
            if items:
                session_pk = items[0]["id"]

        payload = {
            "timestamp":        ts,
            "person_count":     d["person_count"],
            "has_hat":          d["has_hat"],
            "hat_confidence":   round(d["hat_confidence"], 4),
            "has_apron":        d["has_apron"],
            "apron_confidence": round(d["apron_confidence"], 4),
            "is_compliant":     d["is_compliant"],
            "violations":       d["violations"],
            "session":          session_pk,
        }

        if files:
            # multipart/form-data (файл менен)
            form = {k: (None, str(v)) for k, v in payload.items() if v is not None}
            r = requests.post(f"{API_BASE}/records/",
                              data={k: str(v) for k, v in payload.items()},
                              files=files, headers=headers, timeout=10)
        else:
            r = requests.post(f"{API_BASE}/records/",
                              json=payload, headers=headers, timeout=10)

        if r.status_code in (200, 201):
            icon = "✓" if d["is_compliant"] else "✗"
            print(f"[API] {icon} Жаздырылды → id={r.json().get('id')}  "
                  f"(шляпа={'✔' if d['has_hat'] else '✘'} фартук={'✔' if d['has_apron'] else '✘'})")
        elif r.status_code == 401:
            _api_token = None
            print("[API] Token жарабады — кайра кирүүдө…")
        else:
            print(f"[API] Ката {r.status_code}: {r.text[:150]}")
    except Exception as e:
        print(f"[API] Жөнөтүү катасы: {e}")
    finally:
        if tmpf and os.path.exists(tmpf.name):
            try:
                os.unlink(tmpf.name)
            except Exception:
                pass
        for fobj in files.values():
            try:
                fobj[1].close()
            except Exception:
                pass


# ─── Helpers ─────────────────────────────────────────────────────────────────
def parse_args():
    parser = argparse.ArgumentParser(description="Chef Control in Kitchen")
    parser.add_argument("--source",     default=str(config.CAMERA_SOURCE),
                        help="Камера индекси же видео файлдын жолу (демейки: 0)")
    parser.add_argument("--interval",   type=int, default=config.CHECK_INTERVAL_SECONDS,
                        help="Текшерүү интервалы секундта (демейки: 10)")
    parser.add_argument("--no-display", action="store_true",
                        help="Видео терезесин көрсөтпөө")
    parser.add_argument("--no-api",     action="store_true",
                        help="Веб APIга жазбоо (CSV гана)")
    return parser.parse_args()


def open_camera(source: str) -> cv2.VideoCapture:
    """Камераны же видео файлды ачат."""
    src = int(source) if source.isdigit() else source
    cap = cv2.VideoCapture(src)
    if not cap.isOpened():
        raise RuntimeError(f"Камера/видео ачылган жок: {source}")
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  config.FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)
    return cap


def get_timestamp() -> str:
    return datetime.now().strftime("%H:%M:%S")


# ─── Main Loop ───────────────────────────────────────────────────────────────
def run(args):
    global _running

    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    print("=" * 60)
    print("  🍳  Chef Control in Kitchen  —  Баштоо")
    print(f"  Источник      : {args.source}")
    print(f"  Интервал      : {args.interval} секунд")
    print(f"  Сессия        : {session_id}")
    print(f"  Веб API       : {'Өчүрүлгөн' if args.no_api else API_BASE}")
    print(f"  Видео экран   : {'Өчүрүлгөн' if args.no_display else 'Күйгүзүлгөн'}")
    print("=" * 60)

    # API login (background)
    if not args.no_api:
        _api_login()

    detector = ChefComplianceDetector()
    reporter = ReportManager()

    cap          = open_camera(args.source)
    last_check   = time.time() - args.interval   # биринчи текшерүүнү дароо жасасын
    show_video   = config.SHOW_VIDEO and not args.no_display
    latest_frame = None   # экранда уланта туруп бере турган акыркы аннотацияланган кадр

    print("\n[ChefControl] Иштеп жатат. Чыгуу үчүн → Ctrl+C же 'q'\n")

    while _running:
        ret, frame = cap.read()
        if not ret:
            print("[ChefControl] Кадр алынган жок — токтоп жатат.")
            break

        now = time.time()

        # ─── Ар 10 секунтта текшерүү ─────────────────────────────────────
        if now - last_check >= args.interval:
            last_check = now
            timestamp  = get_timestamp()

            print(f"\n[{timestamp}] ── Текшерүү башталды ──────────────────────")
            det = detector.detect(frame, timestamp)
            reporter.log(det, frame)

            # Веб APIга жаз
            if not args.no_api:
                violation_frame = frame if not det.is_compliant else None
                ingest_to_api(det, violation_frame, session_id)

            # Аннотацияланган кадрды сакта (экран үчүн)
            if show_video:
                latest_frame = detector.draw_results(frame, det)

        # ─── Видео экранды жаңылоо ───────────────────────────────────────
        if show_video:
            display = latest_frame if latest_frame is not None else frame

            # Кийинки текшерүүгө канча убакыт калгандыгын көрсөт
            remaining = max(0, int(args.interval - (time.time() - last_check)))
            cv2.putText(display,
                        f"Кийинки текшерүү: {remaining}s",
                        (20, display.shape[0] - 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

            cv2.imshow("Chef Control in Kitchen", display)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    # ─── Жабуу ───────────────────────────────────────────────────────────
    cap.release()
    if show_video:
        cv2.destroyAllWindows()

    reporter.print_session_summary()


# ─── Entry Point ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    args = parse_args()
    run(args)



# ─── Signal handler (Ctrl+C менен чыкканда жыйынтык чыгарсын) ───────────────
_running = True

def _handle_signal(sig, frame_):
    global _running
    print("\n[ChefControl] Токтотулуп жатат…")
    _running = False

signal.signal(signal.SIGINT,  _handle_signal)
signal.signal(signal.SIGTERM, _handle_signal)


# ─── Helpers ─────────────────────────────────────────────────────────────────
def parse_args():
    parser = argparse.ArgumentParser(description="Chef Control in Kitchen")
    parser.add_argument("--source",     default=str(config.CAMERA_SOURCE),
                        help="Камера индекси же видео файлдын жолу (демейки: 0)")
    parser.add_argument("--interval",   type=int, default=config.CHECK_INTERVAL_SECONDS,
                        help="Текшерүү интервалы секундта (демейки: 10)")
    parser.add_argument("--no-display", action="store_true",
                        help="Видео терезесин көрсөтпөө")
    return parser.parse_args()


def open_camera(source: str) -> cv2.VideoCapture:
    """Камераны же видео файлды ачат."""
    src = int(source) if source.isdigit() else source
    cap = cv2.VideoCapture(src)
    if not cap.isOpened():
        raise RuntimeError(f"Камера/видео ачылган жок: {source}")
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  config.FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)
    return cap


def get_timestamp() -> str:
    return datetime.now().strftime("%H:%M:%S")


# ─── Main Loop ───────────────────────────────────────────────────────────────
def run(args):
    global _running

    print("=" * 60)
    print("  🍳  Chef Control in Kitchen  —  Баштоо")
    print(f"  Источник      : {args.source}")
    print(f"  Интервал      : {args.interval} секунд")
    print(f"  Видео экран   : {'Өчүрүлгөн' if args.no_display else 'Күйгүзүлгөн'}")
    print("=" * 60)

    detector = ChefComplianceDetector()
    reporter = ReportManager()

    cap          = open_camera(args.source)
    last_check   = time.time() - args.interval   # биринчи текшерүүнү дароо жасасын
    show_video   = config.SHOW_VIDEO and not args.no_display
    latest_frame = None   # экранда уланта туруп бере турган акыркы аннотацияланган кадр

    print("\n[ChefControl] Иштеп жатат. Чыгуу үчүн → Ctrl+C же 'q'\n")

    while _running:
        ret, frame = cap.read()
        if not ret:
            print("[ChefControl] Кадр алынган жок — токтоп жатат.")
            break

        now = time.time()

        # ─── Ар 10 секунтта текшерүү ─────────────────────────────────────
        if now - last_check >= args.interval:
            last_check = now
            timestamp  = get_timestamp()

            print(f"\n[{timestamp}] ── Текшерүү башталды ──────────────────────")
            det = detector.detect(frame, timestamp)
            reporter.log(det, frame)

            # Аннотацияланган кадрды сакта (экран үчүн)
            if show_video:
                latest_frame = detector.draw_results(frame, det)

        # ─── Видео экранды жаңылоо ───────────────────────────────────────
        if show_video:
            display = latest_frame if latest_frame is not None else frame

            # Кийинки текшерүүгө канча убакыт калгандыгын көрсөт
            remaining = max(0, int(args.interval - (time.time() - last_check)))
            cv2.putText(display,
                        f"Кийинки текшерүү: {remaining}s",
                        (20, display.shape[0] - 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

            cv2.imshow("Chef Control in Kitchen", display)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    # ─── Жабуу ───────────────────────────────────────────────────────────
    cap.release()
    if show_video:
        cv2.destroyAllWindows()

    reporter.print_session_summary()


# ─── Entry Point ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    args = parse_args()
    run(args)
