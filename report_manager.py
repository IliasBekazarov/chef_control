"""
Report Manager — Жыйынтыктарды сактоо жана басып чыгаруу
"""

import os
import csv
import logging
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

import config
from detector import DetectionResult


def _ensure_dirs():
    Path(config.REPORTS_DIR).mkdir(parents=True, exist_ok=True)
    if config.SAVE_VIOLATIONS:
        Path(config.VIOLATIONS_DIR).mkdir(parents=True, exist_ok=True)


def setup_logger() -> logging.Logger:
    _ensure_dirs()
    logger = logging.getLogger("ChefControl")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        # Файлга жазуу
        fh = logging.FileHandler(config.LOG_FILE, encoding="utf-8")
        fh.setFormatter(logging.Formatter("%(asctime)s  %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
        logger.addHandler(fh)

        # Консолго чыгаруу
        ch = logging.StreamHandler()
        ch.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(ch)
    return logger


class ReportManager:
    """Текшерүү жыйынтыктарын CSV жана лог файлдарга жазат."""

    CSV_FILE = Path(config.REPORTS_DIR) / "results.csv"

    def __init__(self):
        _ensure_dirs()
        self.logger  = setup_logger()
        self.session = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._init_csv()
        self.total_checks     = 0
        self.total_violations = 0

    def _init_csv(self):
        if not self.CSV_FILE.exists():
            with open(self.CSV_FILE, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "session", "timestamp", "person_count",
                    "has_hat", "hat_confidence",
                    "has_apron", "apron_confidence",
                    "is_compliant", "violations", "frame_path"
                ])

    # ── Public API ──────────────────────────────────────────────────────────
    def log(self, det: DetectionResult, frame: np.ndarray = None):
        self.total_checks += 1
        if not det.is_compliant:
            self.total_violations += 1

        # Консол + лог файл
        self.logger.info(det.summary())

        # CSV
        with open(self.CSV_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                self.session,
                det.timestamp,
                det.person_count,
                det.has_hat,
                f"{det.hat_confidence:.2f}",
                det.has_apron,
                f"{det.apron_confidence:.2f}",
                det.is_compliant,
                " | ".join(det.violations),
                det.frame_path or "",
            ])

        # Бузуу кадрын сактоо
        if config.SAVE_VIOLATIONS and not det.is_compliant and frame is not None:
            self._save_violation_frame(det, frame)

    def _save_violation_frame(self, det: DetectionResult, frame: np.ndarray):
        fname = f"{config.VIOLATIONS_DIR}/{self.session}_{det.timestamp.replace(':', '-')}.jpg"
        cv2.imwrite(fname, frame)
        det.frame_path = fname

    def print_session_summary(self):
        """Сессиянын жалпы жыйынтыгын чыгаруу."""
        compliance_rate = (
            (self.total_checks - self.total_violations) / self.total_checks * 100
            if self.total_checks > 0 else 0
        )
        summary = (
            "\n" + "═" * 60 + "\n"
            f"  📊  СЕССИЯ ЖЫЙЫНТЫГЫ  [{self.session}]\n"
            "═" * 60 + "\n"
            f"  Жалпы текшерүүлөр    : {self.total_checks}\n"
            f"  Шарт бузуулар        : {self.total_violations}\n"
            f"  Шарт аткаруу пайызы  : {compliance_rate:.1f}%\n"
            f"  Лог файл             : {config.LOG_FILE}\n"
            f"  CSV отчет            : {self.CSV_FILE}\n"
            "═" * 60
        )
        print(summary)
        self.logger.info(summary)
