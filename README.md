# 🍳 Chef Control in Kitchen

Ашпозчунун **шляпасын** жана **фартугун** автоматтык түрдө текшергич.  
Компьютердик көрүү (Computer Vision) жана **YOLOv8** негизинде курулган.

---

## 📋 Долбоордун максаты

Ашканада иштеген ашпозчунун санитардык жабдыктарын (chef hat + apron) **ар 10 секунтта** камера аркылуу текшерип, бузуулар жөнүндө жыйынтык чыгаруу.

---

## 🗂️ Структура

```
chef_control/
├── main.py              # Башкы скрипт
├── detector.py          # ChefComplianceDetector класс
├── report_manager.py    # Жыйынтыктарды сактоо / лог
├── config.py            # Бардык жөндөөлөр
├── requirements.txt     # Python зависимосттор
├── models/              # Custom model (chef_detector.pt) бул жерге
└── reports/
    ├── chef_control.log # Лог файл
    ├── results.csv      # CSV отчет
    └── violations/      # Бузуу кадрларынын сүрөттөрү
```

---

## 🚀 Баштоо

### 1. Талаптарды орнотуу
```bash
pip install -r requirements.txt
```

### 2. Иштетүү

**Webcam менен:**
```bash
python main.py
```

**Видео файл менен:**
```bash
python main.py --source video.mp4
```

**Видео терезесиз (server mode):**
```bash
python main.py --no-display
```

**Интервалды өзгөртүү (мисалы 30 секунд):**
```bash
python main.py --interval 30
```

---

## ⚙️ Жөндөөлөр (`config.py`)

| Параметр | Маани | Маңызы |
|---|---|---|
| `CAMERA_SOURCE` | `0` | Камера индекси же видео жол |
| `CHECK_INTERVAL_SECONDS` | `10` | Текшерүү интервалы (секунд) |
| `DETECTION_CONFIDENCE` | `0.45` | Минималдык ишеним деңгээли |
| `CUSTOM_MODEL_PATH` | `models/chef_detector.pt` | Арнайы окутулган модел |
| `SAVE_VIOLATIONS` | `True` | Бузуу кадрларын сактоо |
| `SHOW_VIDEO` | `True` | Видео терезени көрсөтүү |

---

## 🤖 Модел режимдери

### 1️⃣ Custom Model (Сунушталат)
`models/chef_detector.pt` файлын коюңуз — арнайы окутулган YOLOv8 модели.  
[Roboflow Universe](https://universe.roboflow.com/) же [Kaggle](https://kaggle.com/) дан chef hat / apron dataset табып, YOLOv8 менен окутуңуз.

**Керектүү класстар:**
```
0: person
1: chef_hat
2: apron
3: no_chef_hat
4: no_apron
```

### 2️⃣ Base Mode (Demo)
Custom model жок болсо, `yolov8n.pt` (COCO) модели колдонулат:
- Адамдарды аныктайт
- Шляпа / фартукту HSV ак-пикселдер аркылуу баалайт

---

## 📊 Жыйынтык форматы

**Консол чыгарымы:**
```
[14:35:20]  ❌ ШАРТ БУЗУЛДУ  |  Шляпа: ✘ (0%)  |  Фартук: ✔ (82%)  |  Бузуулар: Шляпа кийилген эмес
[14:35:30]  ✅ ШАРТ АТКАРЫЛДЫ  |  Шляпа: ✔ (91%)  |  Фартук: ✔ (87%)
```

**Сессия жыйынтыгы:**
```
════════════════════════════════════════════════════════════
  📊  СЕССИЯ ЖЫЙЫНТЫГЫ  [20260419_143500]
════════════════════════════════════════════════════════════
  Жалпы текшерүүлөр    : 36
  Шарт бузуулар        : 4
  Шарт аткаруу пайызы  : 88.9%
  Лог файл             : reports/chef_control.log
  CSV отчет            : reports/results.csv
════════════════════════════════════════════════════════════
```

---

## 🏋️ Custom Model Окутуу (Кыскача)

```bash
# 1. Dataset жүктөп алыңыз (Roboflow YOLO format)
# 2. Окутуу
pip install ultralytics
yolo train data=chef_dataset.yaml model=yolov8n.pt epochs=50 imgsz=640

# 3. Даяр болгон модел:  runs/detect/train/weights/best.pt
# 4. Аны  models/chef_detector.pt  деп сактаңыз
```
