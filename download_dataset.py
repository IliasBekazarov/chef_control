"""
Roboflow Dataset Жүктөгүч
=========================
Иштетүү: python download_dataset.py

Нускама:
1. https://app.roboflow.com → Account → Settings → API Keys
2. API ключиңизди төмөндө ROBOFLOW_API_KEY орнуна коюңуз
3. Dataset URL: https://universe.roboflow.com/<workspace>/<project>
   - workspace  → WORKSPACE
   - project    → PROJECT
   - version    → VERSION (1, 2, 3 …)
"""

from roboflow import Roboflow
from pathlib import Path
import shutil, os

# ══════════════════════════════════════════════════════════════════
# 👇  ОСУ ЖЕРДИ ТОЛТУРУҢУЗ
# ══════════════════════════════════════════════════════════════════
ROBOFLOW_API_KEY = "eE1XYH10Ib4AjarfnRM7"   # app.roboflow.com → Settings → API

# Dataset URL: https://universe.roboflow.com/<workspace>/<project>/<version>
WORKSPACE   = "ilias-beknazarov-s-workspace"   # Roboflow workspace
PROJECT     = "chef-hat-detection-pb8yw"       # Project slug
VERSION     = 1                                # Версия номери (сан)
# ══════════════════════════════════════════════════════════════════

DEST_DIR    = "datasets/chef_dataset"
EXPORT_DIR  = "datasets/chef_dataset_yolo"   # YOLOv8 форматы

def download():
    print(f"\n📦  Roboflow dataset жүктөлүүдө…")
    print(f"    Workspace : {WORKSPACE}")
    print(f"    Project   : {PROJECT}")
    print(f"    Version   : {VERSION}\n")

    rf      = Roboflow(api_key=ROBOFLOW_API_KEY)
    project = rf.workspace(WORKSPACE).project(PROJECT)
    dataset = project.version(VERSION).download("yolov8", location=DEST_DIR)

    print(f"\n✅  Dataset жүктөлдү: {DEST_DIR}")
    print(f"    data.yaml жолу   : {DEST_DIR}/data.yaml")

    # data.yaml файлын текшер
    yaml_path = Path(DEST_DIR) / "data.yaml"
    if yaml_path.exists():
        print("\n── data.yaml мазмуну ─────────────────────────────")
        print(yaml_path.read_text())
        print("──────────────────────────────────────────────────")
    else:
        print("⚠️  data.yaml табылган жок — папканы текшериңиз.")


def print_train_command():
    """Окутуу командасын чыгарат."""
    yaml_path = Path(DEST_DIR) / "data.yaml"
    print("\n" + "═"*55)
    print("  🏋️  DATASET ДАЯР — ОКУТУУ КОМАНДАСЫ:")
    print("═"*55)
    print(f"  yolo train \\")
    print(f"    data={yaml_path} \\")
    print(f"    model=yolov8n.pt \\")
    print(f"    epochs=50 \\")
    print(f"    imgsz=640 \\")
    print(f"    batch=16 \\")
    print(f"    name=chef_detector")
    print("═"*55)
    print("  Окутуу бүткөндөн кийин:")
    print("  runs/detect/chef_detector/weights/best.pt → models/chef_detector.pt")
    print("═"*55 + "\n")


if __name__ == "__main__":
    if ROBOFLOW_API_KEY == "СИЗДИН_API_КЛЮЧ":
        print("\n❌  Ката: API ключиңизди download_dataset.py га коюңуз!")
        print("   app.roboflow.com → Settings → Roboflow API\n")
        exit(1)

    download()
    print_train_command()
