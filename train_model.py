"""
Chef Control — YOLOv8 Model Training
Apple Silicon MPS GPU колдоосу менен.

Иштетүү:
    python train_model.py                        # yolov8s, 100 epoch, MPS
    python train_model.py --model yolov8n        # тез (жакшы эмес)
    python train_model.py --epochs 50            # аз эпох
    python train_model.py --resume               # улантуу
    python train_model.py --validate-only        # модел текшерүү гана
"""

import argparse
import shutil
import sys
import json
from pathlib import Path
from datetime import datetime

DATA_YAML        = "datasets/chef_dataset/data.yaml"
OUTPUT_DIR       = "models"
MODEL_NAME       = "chef_detector_v2"
STATUS_FILE      = "runs/training_status.json"


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--model",          default="yolov8s.pt")
    p.add_argument("--epochs",         type=int,   default=100)
    p.add_argument("--imgsz",          type=int,   default=640)
    p.add_argument("--batch",          type=int,   default=16)
    p.add_argument("--device",         default="mps",
                   help="Тренинг device: mps | cpu | 0 (CUDA)")
    p.add_argument("--resume",         action="store_true")
    p.add_argument("--data",           default=DATA_YAML)
    p.add_argument("--validate-only",  action="store_true")
    return p.parse_args()


def write_status(status: dict):
    Path(STATUS_FILE).parent.mkdir(parents=True, exist_ok=True)
    with open(STATUS_FILE, "w") as f:
        json.dump(status, f, indent=2)


def read_results_csv(run_dir: Path) -> list:
    results_csv = run_dir / "results.csv"
    if not results_csv.exists():
        return []
    import csv
    return list(csv.DictReader(open(results_csv)))


def check_dataset(data_yaml: str) -> bool:
    path = Path(data_yaml)
    if not path.exists():
        print(f"\n❌  Dataset табылган жок: {data_yaml}")
        return False
    import yaml
    with open(path) as f:
        cfg = yaml.safe_load(f)
    train_dir = Path(cfg.get("train", ""))
    val_dir   = Path(cfg.get("val",   ""))
    tc = len(list(train_dir.glob("*"))) if train_dir.exists() else 0
    vc = len(list(val_dir.glob("*")))   if val_dir.exists()   else 0
    print(f"  Dataset  : train={tc} сүрөт, val={vc} сүрөт")
    print(f"  Класстар : {cfg.get('nc')} — {cfg.get('names')}")
    return tc > 0


def train(args):
    import torch
    from ultralytics import YOLO

    # Device тандоо
    device = args.device
    if device == "mps" and not torch.backends.mps.is_available():
        print("  ⚠️  MPS жок → CPU колдонулат")
        device = "cpu"
    if device == "mps":
        print(f"  🍎  Apple Silicon MPS GPU — тренинг тездетилет!")

    if not check_dataset(args.data):
        sys.exit(1)

    write_status({
        "state":       "training",
        "model_name":  MODEL_NAME,
        "base_model":  args.model,
        "device":      device,
        "epochs_total":args.epochs,
        "epoch":       0,
        "map50":       0.0,
        "map50_best":  0.0,
        "started_at":  datetime.now().isoformat(),
        "finished_at": None,
        "error":       None,
    })

    print("\n" + "═" * 58)
    print("  🏋️  YOLOv8 ТРЕНИНГ БАШТАЛДЫ")
    print("═" * 58)
    print(f"  Базалык модел : {args.model}")
    print(f"  Device        : {device}")
    print(f"  Epochs        : {args.epochs}")
    print(f"  Image size    : {args.imgsz}×{args.imgsz}")
    print(f"  Натыйжа       : runs/detect/{MODEL_NAME}/weights/best.pt")
    print("═" * 58)

    if args.resume:
        ckpt = Path(f"runs/detect/{MODEL_NAME}/weights/last.pt")
        model = YOLO(str(ckpt) if ckpt.exists() else args.model)
    else:
        model = YOLO(args.model)

    try:
        model.train(
            data          = args.data,
            epochs        = args.epochs,
            imgsz         = args.imgsz,
            batch         = args.batch,
            name          = MODEL_NAME,
            device        = device,
            # LR — cosine annealing: 0.01 → 0.001
            lr0           = 0.01,
            lrf           = 0.1,
            cos_lr        = True,
            warmup_epochs = 3,
            # Early stopping
            patience      = 25,
            # Augmentation — dataset аз болгондо маанилүү
            hsv_h         = 0.02,
            hsv_s         = 0.75,
            hsv_v         = 0.45,
            fliplr        = 0.5,
            flipud        = 0.0,
            mosaic        = 1.0,
            mixup         = 0.15,
            copy_paste    = 0.1,
            degrees       = 10.0,
            translate     = 0.1,
            scale         = 0.5,
            close_mosaic  = 15,
            # Output
            plots         = True,
            save          = True,
            resume        = args.resume,
            verbose       = True,
        )
    except Exception as e:
        write_status({
            "state": "error",
            "error": str(e),
            "finished_at": datetime.now().isoformat(),
        })
        raise

    # ── Жыйынтык ─────────────────────────────────────────────────
    run_dir  = Path(f"runs/detect/{MODEL_NAME}")
    best_pt  = run_dir / "weights/best.pt"
    rows     = read_results_csv(run_dir)
    best_map = max((float(r.get("metrics/mAP50(B)", 0)) for r in rows), default=0.0)

    # best.pt → models/chef_detector.pt
    if best_pt.exists():
        Path(OUTPUT_DIR).mkdir(exist_ok=True)
        dest = Path(OUTPUT_DIR) / "chef_detector.pt"
        shutil.copy2(best_pt, dest)
        print(f"\n  📦  Модел сакталды: {dest}  ({dest.stat().st_size/1024/1024:.1f} MB)")

    grade = ("🟢 МЫКТЫ" if best_map >= 0.90 else
             "🟡 ЖАКШЫ" if best_map >= 0.75 else "🔴 ЖЕТИШСИЗ")

    print(f"\n  📊  Эң жакшы mAP50: {best_map:.3f} ({best_map*100:.1f}%)  {grade}")
    print(f"  🚀  Детектор: python main.py --source 0")

    write_status({
        "state":        "done",
        "model_name":   MODEL_NAME,
        "epochs_total": len(rows),
        "map50_best":   round(best_map, 4),
        "map50":        round(best_map, 4),
        "finished_at":  datetime.now().isoformat(),
        "error":        None,
    })


def validate_model(data_yaml: str):
    from ultralytics import YOLO
    dest = Path(OUTPUT_DIR) / "chef_detector.pt"
    print(f"\n🔍  Модел текшерилүүдө: {dest}")
    model = YOLO(str(dest))
    metrics = model.val(data=data_yaml, imgsz=640, batch=8, verbose=False, device="cpu")
    grade = ("🟢 МЫКТЫ" if metrics.box.map50 >= 0.90 else
             "🟡 ЖАКШЫ" if metrics.box.map50 >= 0.75 else "🔴 ЖЕТИШСИЗ")
    print(f"  mAP50    : {metrics.box.map50:.3f} ({metrics.box.map50*100:.1f}%)  {grade}")
    print(f"  mAP50-95 : {metrics.box.map:.3f}")
    print(f"  Precision: {metrics.box.mp:.3f}")
    print(f"  Recall   : {metrics.box.mr:.3f}")


if __name__ == "__main__":
    args = parse_args()
    print(f"\n{'╔'+'═'*54+'╗'}")
    print(f"{'║':1}{'  Chef Control — YOLOv8 Training':^54}{'║':1}")
    print(f"{'╚'+'═'*54+'╝'}")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if args.validate_only:
        validate_model(args.data)
    else:
        train(args)
