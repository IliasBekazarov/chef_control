"""
Chef Control - Configuration Settings
Проект: Chef Control in Kitchen
Максаты: Ашпозчунун шляпасы жана фартугун текшеруу
"""

# ─── Camera / Video Settings ────────────────────────────────────────────────
CAMERA_SOURCE = 0           # 0 = default webcam, же видео файлдын жолу
FRAME_WIDTH   = 1280
FRAME_HEIGHT  = 720

# ─── Detection Settings ─────────────────────────────────────────────────────
CHECK_INTERVAL_SECONDS = 10        # ар 10 секунтта текшеруу
DETECTION_CONFIDENCE   = 0.45      # минималдык ишеним деңгээли
IOU_THRESHOLD          = 0.45

# YOLOv8 model path (custom trained model)
# Эгер custom model жок болсо → base YOLOv8n колдонулат
CUSTOM_MODEL_PATH = "models/chef_detector.pt"
BASE_MODEL_PATH   = "yolov8n.pt"

# ─── PPE Classes — datasets/chef_dataset/data.yaml дан алынды ───────────────
CLASS_NAMES = {
    0: "Chef-Hat",           # шляпа кийген
    1: "No_Hat",             # шляпасы жок
    2: "glove",              # колкап
    3: "hand",               # кол
    4: "hat_without-hat",    # аралаш
    5: "withhat",            # шляпа бар (альтернатив)
    6: "without_hat",        # шляпасы жок (альтернатив)
}

# Шляпа "бар" деп эсептелүүчү класстар
HAT_PRESENT_CLASSES    = {"Chef-Hat", "withhat"}
# Шляпа "жок" деп эсептелүүчү класстар
HAT_ABSENT_CLASSES     = {"No_Hat", "without_hat", "hat_without-hat"}

# ─── Apron HSV Detection ──────────────────────────────────────────────────────
# Адамдын кеуде зонасынын канча пайызы апрон түсү болсо "кийген" деп эсептелет
# 0.18 = 18% (туурасын жөндөө үчүн 0.10 – 0.25 аралыгында өзгөртүңүз)
APRON_HSV_THRESHOLD    = 0.18

# ─── Report / Logging Settings ───────────────────────────────────────────────
REPORTS_DIR      = "reports"
LOG_FILE         = "reports/chef_control.log"
SAVE_VIOLATIONS  = True      # шарт бузуу учурларын сүрөт катары сактоо
VIOLATIONS_DIR   = "reports/violations"

# ─── Display Settings ────────────────────────────────────────────────────────
SHOW_VIDEO       = True
DRAW_BOXES       = True

# Colors (BGR)
COLOR_OK         = (0, 200, 0)     # жашыл — шарт аткарылды
COLOR_VIOLATION  = (0, 0, 220)     # кызыл  — шарт бузулду
COLOR_WARNING    = (0, 165, 255)   # сарымтыл — эскертуу
COLOR_TEXT       = (255, 255, 255) # ак текст
