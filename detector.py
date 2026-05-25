"""
Chef Compliance Detector
Ашпозчунун шляпасы (chef hat) жана фартугун (apron) аныктоо модули
"""

import os
import cv2
import numpy as np
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

import config


@dataclass
class DetectionResult:
    """Бир текшерүүнүн жыйынтыгы"""
    timestamp: str
    person_count: int = 0
    # Hat stats
    has_hat: bool = False
    hat_confidence: float = 0.0
    # Apron stats
    has_apron: bool = False
    apron_confidence: float = 0.0
    # Overall compliance
    is_compliant: bool = False
    violations: list = field(default_factory=list)
    frame_path: Optional[str] = None   # сакталган сүрөттүн жолу

    def summary(self) -> str:
        """Кыска жыйынтык тексти"""
        status = "✅ ШАРТ АТКАРЫЛДЫ" if self.is_compliant else "❌ ШАРТ БУЗУЛДУ"
        hat_s   = f"Шляпа: {'✔' if self.has_hat  else '✘'} ({self.hat_confidence:.0%})"
        apron_s = f"Фартук: {'✔' if self.has_apron else '✘'} ({self.apron_confidence:.0%})"
        viols   = "  |  Бузуулар: " + ", ".join(self.violations) if self.violations else ""
        return f"[{self.timestamp}]  {status}  |  {hat_s}  |  {apron_s}{viols}"


class ChefComplianceDetector:
    """
    YOLOv8 негизиндеги ашпозчунун жабдыктарын текшергич.

    Эгер арнайы окутулган (custom) модел жок болсо,
    YOLOv8 базалык модели менен адамды аныктайт жана
    шляпа/фартукту аныктоону имитациялайт (demo mode).
    """

    def __init__(self):
        self.model = None
        self.use_custom = False
        self._load_model()

    # ─── Model Loading ────────────────────────────────────────────────────────
    def _load_model(self):
        from ultralytics import YOLO

        custom_path = Path(config.CUSTOM_MODEL_PATH)
        if custom_path.exists():
            print(f"[Detector] Custom model жүктөлүүдө: {custom_path}")
            self.model = YOLO(str(custom_path))
            self.use_custom = True
        else:
            print(f"[Detector] Custom model табылган жок → базалык модел колдонулат: {config.BASE_MODEL_PATH}")
            self.model = YOLO(config.BASE_MODEL_PATH)
            self.use_custom = False

    # ─── Core Detection ───────────────────────────────────────────────────────
    def detect(self, frame: np.ndarray, timestamp: str) -> DetectionResult:
        """
        Берилген кадрды талдап, DetectionResult кайтарат.
        """
        results_raw = self.model(
            frame,
            conf=config.DETECTION_CONFIDENCE,
            iou=config.IOU_THRESHOLD,
            verbose=False,
        )[0]

        if self.use_custom:
            return self._parse_custom(results_raw, frame, timestamp)
        else:
            return self._parse_base(results_raw, frame, timestamp)

    # ── Custom model parser ───────────────────────────────────────────────────
    def _parse_custom(self, results, frame: np.ndarray, timestamp: str) -> DetectionResult:
        """
        Dataset класстары:
          0: Chef-Hat   1: No_Hat   2: glove   3: hand
          4: hat_without-hat   5: withhat   6: without_hat

        Апрон: dataset да класс жок → YOLO person bbox + HSV менен аныкталат.
        """
        boxes = results.boxes
        res   = DetectionResult(timestamp=timestamp)

        if boxes is None or len(boxes) == 0:
            res.violations = ["Эч ким аныкталган жок"]
            return res

        best_hat_conf    = 0.0
        best_no_hat_conf = 0.0
        person_boxes     = []   # апрон үчүн адам bbox лары

        for box in boxes:
            cls_id = int(box.cls[0])
            conf   = float(box.conf[0])
            name   = config.CLASS_NAMES.get(cls_id, "unknown")
            xyxy   = box.xyxy[0].cpu().numpy().astype(int)  # [x1,y1,x2,y2]

            if name in config.HAT_PRESENT_CLASSES:
                best_hat_conf = max(best_hat_conf, conf)
                # Шляпа bbox → адам bbox катары да колдонобуз
                person_boxes.append(xyxy)
            elif name in config.HAT_ABSENT_CLASSES:
                best_no_hat_conf = max(best_no_hat_conf, conf)
                person_boxes.append(xyxy)

        res.person_count = len(person_boxes) if person_boxes else 1

        # ── Шляпа чечими ──────────────────────────────────────────────────
        res.has_hat        = (best_hat_conf >= config.DETECTION_CONFIDENCE and
                              best_hat_conf >= best_no_hat_conf)
        res.hat_confidence = best_hat_conf if res.has_hat else best_no_hat_conf

        # ── Апрон: YOLO bbox зонасында HSV текшеруу ───────────────────────
        has_apron, apron_conf = self._detect_apron_in_person(frame, person_boxes)
        res.has_apron         = has_apron
        res.apron_confidence  = apron_conf

        # ── Бузуулар ──────────────────────────────────────────────────────
        if not res.has_hat:
            res.violations.append("Шляпа кийилген эмес")
        if not res.has_apron:
            res.violations.append("Фартук кийилген эмес")

        res.is_compliant = res.has_hat and res.has_apron
        return res

    # ── Base model parser (demo / fallback) ──────────────────────────────────
    def _parse_base(self, results, frame: np.ndarray, timestamp: str) -> DetectionResult:
        """
        Базалык COCO модели менен ишлөө:
        - Адамдарды (class 0) аныктайт
        - Шляпа/фартукту аныктоо үчүн HSV сегментацияны колдонот
        """
        boxes  = results.boxes
        res    = DetectionResult(timestamp=timestamp)

        if boxes is None or len(boxes) == 0:
            res.violations = ["Адам аныкталган жок"]
            return res

        # Адамдарды эсепте
        for box in boxes:
            if int(box.cls[0]) == 0:
                res.person_count += 1

        if res.person_count == 0:
            res.violations = ["Адам аныкталган жок"]
            return res

        # Жакшыртылган апрон аныктоо (person bbox + HSV)
        person_bboxes = []
        if boxes is not None:
            for box in boxes:
                if int(box.cls[0]) == 0:
                    person_bboxes.append(box.xyxy[0].cpu().numpy().astype(int))

        has_hat, hat_conf     = self._detect_white_hat(frame)
        has_apron, apron_conf = self._detect_apron_in_person(frame, person_bboxes)

        res.has_hat          = has_hat
        res.hat_confidence   = hat_conf
        res.has_apron        = has_apron
        res.apron_confidence = apron_conf

        if not res.has_hat:
            res.violations.append("Шляпа кийилген эмес")
        if not res.has_apron:
            res.violations.append("Фартук кийилген эмес")

        res.is_compliant = res.has_hat and res.has_apron
        return res

    # ─── HSV Helpers ──────────────────────────────────────────────────────────
    def _detect_apron_in_person(self, frame: np.ndarray, person_boxes: list):
        """
        Адамдын bbox ынын кеуде-курсак зонасында апронду аныктайт.

        Стратегия:
        1. Эгер YOLO дан bbox бар → ошол bbox нын орто 40%-ын карайт
        2. Bbox жок болсо → кадрдын ортосун карайт
        3. Ак (chef apron), ачык көк же кара апрондорду аныктайт
        """
        h, w = frame.shape[:2]

        if person_boxes:
            # Бардык bbox лардын бириктирилген зонасын алабыз
            x1 = min(b[0] for b in person_boxes)
            y1 = min(b[1] for b in person_boxes)
            x2 = max(b[2] for b in person_boxes)
            y2 = max(b[3] for b in person_boxes)
            # Кеуде-курсак зонасы: bbox нын 25%-75% аралыгы (жогорку кийим аймагы)
            ph   = y2 - y1
            ry1  = int(y1 + ph * 0.25)
            ry2  = int(y1 + ph * 0.80)
            rx1  = max(0, x1)
            rx2  = min(w, x2)
        else:
            # Bbox жок → кадрдын орто зонасы
            ry1, ry2 = h // 4, int(h * 0.80)
            rx1, rx2 = w // 5, 4 * w // 5

        roi = frame[max(0, ry1):min(h, ry2), rx1:rx2]
        if roi.size == 0:
            return False, 0.0

        # Апрон түс маскалары (HSV)
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

        # 1) Ак апрон (классикалык chef apron)
        mask_white = cv2.inRange(hsv, (0, 0, 170), (180, 45, 255))

        # 2) Ачык көк / цвет апрон
        mask_blue  = cv2.inRange(hsv, (90, 40, 80), (140, 255, 255))

        # 3) Кара апрон
        mask_black = cv2.inRange(hsv, (0, 0, 0), (180, 80, 60))

        # Бардык маскаларды бириктир
        mask_all = cv2.bitwise_or(mask_white, cv2.bitwise_or(mask_blue, mask_black))

        # Морфологиялык тазалоо (шыбак пикселдерди алып салуу)
        kernel   = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
        mask_all = cv2.morphologyEx(mask_all, cv2.MORPH_OPEN,  kernel)
        mask_all = cv2.morphologyEx(mask_all, cv2.MORPH_CLOSE, kernel)

        total  = roi.shape[0] * roi.shape[1]
        ratio  = float(cv2.countNonZero(mask_all)) / total if total > 0 else 0.0

        # Апрон threshold: кеуде зонасынын кеминде 18% жарык/апрон пиксели
        has_apron = ratio >= config.APRON_HSV_THRESHOLD
        return has_apron, round(ratio, 2)

    def _detect_white_hat(self, frame: np.ndarray):
        """Кадрдын жогору жагында ак пикселдерди издейт (шляпа зонасы)."""
        h, w = frame.shape[:2]
        roi  = frame[0 : h // 3, w // 4 : 3 * w // 4]
        conf = self._white_ratio(roi)
        return conf > 0.12, round(conf, 2)

    @staticmethod
    def _white_ratio(roi: np.ndarray) -> float:
        """ROI-дагы ак пикселдердин үлүшүн эсептейт."""
        if roi.size == 0:
            return 0.0
        hsv   = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        mask  = cv2.inRange(hsv, (0, 0, 180), (180, 40, 255))
        total = roi.shape[0] * roi.shape[1]
        return float(cv2.countNonZero(mask)) / total if total > 0 else 0.0

    # ─── Drawing ──────────────────────────────────────────────────────────────
    def draw_results(self, frame: np.ndarray, det: DetectionResult) -> np.ndarray:
        """Текшерүү жыйынтыгын кадрга тартат."""
        annotated = frame.copy()
        h, w = annotated.shape[:2]
        overlay  = annotated.copy()
        bar_h    = 90
        cv2.rectangle(overlay, (0, 0), (w, bar_h), (30, 30, 30), -1)
        cv2.addWeighted(overlay, 0.65, annotated, 0.35, 0, annotated)

        status_color = config.COLOR_OK if det.is_compliant else config.COLOR_VIOLATION
        status_text  = "COMPLIANT ✓" if det.is_compliant else "VIOLATION ✗"

        cv2.putText(annotated, status_text,  (20, 35),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.1, status_color, 2)
        cv2.putText(annotated, f"Chef Hat: {'YES' if det.has_hat else 'NO'} ({det.hat_confidence:.0%})",
                    (20, 62), cv2.FONT_HERSHEY_SIMPLEX, 0.65, config.COLOR_TEXT, 1)
        cv2.putText(annotated, f"Apron:    {'YES' if det.has_apron else 'NO'} ({det.apron_confidence:.0%})",
                    (350, 62), cv2.FONT_HERSHEY_SIMPLEX, 0.65, config.COLOR_TEXT, 1)
        cv2.putText(annotated, f"Time: {det.timestamp}",
                    (w - 350, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.6, config.COLOR_TEXT, 1)

        if det.violations:
            viol_text = "  |  ".join(det.violations)
            cv2.putText(annotated, viol_text, (20, 85),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, config.COLOR_VIOLATION, 1)
        return annotated
