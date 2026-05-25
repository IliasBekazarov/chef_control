"""
╔══════════════════════════════════════════════════════════╗
║          Chef Control — Model Training Script            ║
║   YOLOv8 менен chef hat жана PPE моделин окутуу          ║
╚══════════════════════════════════════════════════════════╝

Иштетүү:
    python train_model.py                  # демейки
    python train_model.py --epochs 100     # epochs саны
    python train_model.py --model yolov8s  # чоңураак модель
    python train_model.py --resume         # токтогон жерден улантуу

Кадамдар:
    1. Dataset даяр болушу керек: datasets/chef_dataset/data.yaml
       Эгер жок болсо: python download_dataset.py
    2. Скрипт иштетилет
    3. Окутуу бүткөндөн кийин best.pt автоматтык models/ га көчүрүлөт
"""

import argparse
import shutil
from pathlib import Path
from datetime import datetime


# ─── Конфигурация ───────────────────────────────────────────────────────────
DATA_YAML   = "datasets/chef_dataset/data.yaml"   # dataset конфигурациясы
OUTPUT_DIR  = "models"                             # даяр модель сакталган жер
MODEL_NAME  = "chef_detector"                      # runs/detect/<MODEL_NAME>

# YOLOv8 модель варианттары:
#   yolov8n — nano    (эң кичинекей, эң тез,   6.3 MB)  ← демейки
#   yolov8s — small   (орто тез,               22.5 MB)
#   yolov8m — medium  (жай, так,               52.2 MB)
DEFAULT_BASE_MODEL = "yolov8n.pt"
DEFAULT_EPOCHS     = 50
DEFAULT_IMGSZ      = 640
DEFAULT_BATCH      = 16


# ─── Аргументтер ────────────────────────────────────────────────────────────
def parse_args():
    p = argparse.ArgumentParser(description="Chef Control Model Training")
    p.add_argument("--model",   default=DEFAULT_BASE_MODEL,
                   help=f"Базалык YOLOv8 модели (демейки: {DEFAULT_BASE_MODEL})")
    p.add_argument("--epochs",  type=int, default=DEFAULT_EPOCHS,
                   help=f"Эпох саны (демейки: {DEFAULT_EPOCHS})")
    p.add_argument("--imgsz",   type=int, default=DEFAULT_IMGSZ,
                   help=f"Сүрөт өлчөмү (демейки: {DEFAULT_IMGSZ})")
    p.add_argument("--batch",   type=int, default=DEFAULT_BATCH,
                   help=f"Batch өлчөмү (демейки: {DEFAULT_BATCH})")
    p.add_argument("--resume",  action="store_true",
                   help="Акыркы checkpoint'тан улантуу")
    p.add_argument("--data",    default=DATA_YAML,
                   help=f"data.yaml жолу (демейки: {DATA_YAML})")
    return p.parse_args()


# ─── Dataset Текшеруу ───────────────────────────────────────────────────────
def check_dataset(data_yaml: str) -> bool:
    """data.yaml жана сүрөттөр бар экенин текшерет."""
    path = Path(data_yaml)
    if not path.exists():
        print(f"\n❌  Dataset табылган жок: {data_yaml}")
        print("   Алгач dataset жүктөңүз:")
        print("   python download_dataset.py\n")
        return False

    import yaml
    with open(path) as f:
        cfg = yaml.safe_load(f)

    train_dir = Path(cfg.get("train", ""))
    val_dir   = Path(cfg.get("val",   ""))

    train_count = len(list(train_dir.glob("*"))) if train_dir.exists() else 0
    val_count   = len(list(val_dir.glob("*")))   if val_dir.exists()   else 0

    print(f"\n📂  Dataset статусу:")
    print(f"   Train     : {train_count} сүрөт  ({train_dir})")
    print(f"   Validation: {val_count} сүрөт  ({val_dir})")
    print(f"   Класстар  : {cfg.get('nc', '?')} — {cfg.get('names', [])}")

    if train_count == 0:
        print("\n❌  Train сүрөттөрү жок!")
        return False

    return True


# ─── Training ────────────────────────────────────────────────────────────────
def train(args):
    from ultralytics import YOLO

    # Dataset текшерүү
    if not check_dataset(args.data):
        return

    print("\n" + "═" * 60)
    print("  🏋️  YOLOv8 МОДЕЛЬ ОКУТУУ БАШТАЛДЫ")
    print("═" * 60)
    print(f"  Базалык модель : {args.model}")
    print(f"  Dataset        : {args.data}")
    print(f"  Epochs         : {args.epochs}")
    print(f"  Image size     : {args.imgsz}×{args.imgsz}")
    print(f"  Batch size     : {args.batch}")
    print(f"  Resume         : {args.resume}")
    print(f"  Натыйжа        : runs/detect/{MODEL_NAME}/weights/best.pt")
    print("═" * 60)
    print()

    # YOLOv8 модель жүктөө
    if args.resume:
        # Акыркы checkpoint'тан улантуу
        last_ckpt = Path(f"runs/detect/{MODEL_NAME}/weights/last.pt")
        if last_ckpt.exists():
            print(f"  ▶ Улантуу: {last_ckpt}")
            model = YOLO(str(last_ckpt))
        else:
            print(f"  ⚠️  last.pt табылган жок, нөлдөн баштоо…")
            model = YOLO(args.model)
    else:
        model = YOLO(args.model)

    # ─── TRAINING ────────────────────────────────────────────────
    results = model.train(
        data     = args.data,          # datasets/chef_dataset/data.yaml
        epochs   = args.epochs,        # 50
        imgsz    = args.imgsz,         # 640
        batch    = args.batch,         # 16
        name     = MODEL_NAME,         # runs/detect/chef_detector/
        patience = 15,                 # early stopping (15 epoch жакшыланбаса токто)
        cache    = False,              # RAM кэш (жаш RAM болсо True)
        device   = "cpu",             # Mac'та CPU (GPU жок болсо)
        # Augmentation — overfitting болтурбоо үчүн
        hsv_h    = 0.015,
        hsv_s    = 0.7,
        hsv_v    = 0.4,
        flipud   = 0.0,
        fliplr   = 0.5,
        mosaic   = 1.0,
        mixup    = 0.1,
        # Logging
        plots    = True,               # confusion matrix, PR curve ж.б. сакта
        save     = True,               # weights сакта
        resume   = args.resume,
    )

    # ─── Жыйынтык ────────────────────────────────────────────────
    print("\n" + "═" * 60)
    print("  ✅  ОКУТУУ БҮТТҮ!")
    print("═" * 60)

    best_pt = Path(f"runs/detect/{MODEL_NAME}/weights/best.pt")
    if best_pt.exists():
        # best.pt → models/chef_detector.pt
        Path(OUTPUT_DIR).mkdir(exist_ok=True)
        dest = Path(OUTPUT_DIR) / "chef_detector.pt"
        shutil.copy2(best_pt, dest)
        print(f"\n  📦  Модель сакталды: {dest}")
        print(f"      Размер: {dest.stat().st_size / 1024 / 1024:.1f} MB")

    # Metrics чыгаруу
    print_metrics(Path(f"runs/detect/{MODEL_NAME}"))

    print(f"\n  🚀  Детектор баштоо:")
    print(f"      python main.py --source 0")
    print("═" * 60 + "\n")


# ─── Metrics чыгаруу ─────────────────────────────────────────────────────────
def print_metrics(run_dir: Path):
    """Training натыйжаларын консолго чыгарат."""
    results_csv = run_dir / "results.csv"
    if not results_csv.exists():
        return

    import csv
    rows = list(csv.DictReader(open(results_csv)))
    if not rows:
        return

    # Акыркы epoch
    last = rows[-1]
    best_map50 = max(float(r.get("metrics/mAP50(B)", 0)) for r in rows)

    print(f"\n  📊  НАТЫЙЖАЛАР:")
    print(f"   Жалпы epochs         : {len(rows)}")
    print(f"   Эң жакшы mAP50       : {best_map50:.3f}  ({best_map50*100:.1f}%)")
    print(f"   Акыркы epoch box loss: {float(last.get('train/box_loss', 0)):.4f}")
    print(f"   Акыркы val mAP50     : {float(last.get('metrics/mAP50(B)', 0)):.3f}")

    # Рейтинг
    if best_map50 >= 0.90:
        grade = "🟢 МЫКТЫ (>90%)"
    elif best_map50 >= 0.75:
        grade = "🟡 ЖАКШЫ (75–90%)"
    else:
        grade = "🔴 ЖЕТИШСИЗ (<75%)"
    print(f"   Баа                  : {grade}")


# ─── Validate ────────────────────────────────────────────────────────────────
def validate(model_path: str, data_yaml: str):
    """Даяр моделди validation dataset менен текшерет."""
    from ultralytics import YOLO

    print(f"\n🔍  Модель текшерилүүдө: {model_path}")
    model = YOLO(model_path)
    metrics = model.val(
        data   = data_yaml,
        imgsz  = 640,
        batch  = 16,
        verbose= True,
    )
    print(f"\n  mAP50    : {metrics.box.map50:.3f}")
    print(f"  mAP50-95 : {metrics.box.map:.3f}")
    print(f"  Precision: {metrics.box.mp:.3f}")
    print(f"  Recall   : {metrics.box.mr:.3f}")


# ─── Entry Point ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    args = parse_args()

    print("\n" + "╔" + "═"*56 + "╗")
    print("║        Chef Control — Model Training Script          ║")
    print("╚" + "═"*56 + "╝")
    print(f"  Убакыт: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    train(args)
