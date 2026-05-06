# src/evaluate_model.py

import os
from ultralytics import YOLO
import matplotlib.pyplot as plt

def main():
    # ✅ Path to your best model weights
    model_path = r"runs/train/weapon_detector2/weights/best.pt"
    data_path = r"data/dataset.yaml"

    # ✅ Load trained model
    model = YOLO(model_path)

    # ✅ Run validation again (this returns metrics)
    print("🔍 Running YOLO model evaluation...")
    results = model.val(data=data_path, save=True, imgsz=640)

    # ✅ Extract metrics
    metrics = results.results_dict
    precision = metrics.get('metrics/precision(B)', 0)
    recall = metrics.get('metrics/recall(B)', 0)
    map50 = metrics.get('metrics/mAP50(B)', 0)
    map5095 = metrics.get('metrics/mAP50-95(B)', 0)

    # ✅ Display numeric results
    print(f"\n📊 Model Evaluation Results:")
    print(f"Precision: {precision:.4f}")
    print(f"Recall: {recall:.4f}")
    print(f"mAP@50: {map50:.4f}")
    print(f"mAP@50-95: {map5095:.4f}")

    # ✅ Plot metrics
    metrics_names = ["Precision", "Recall", "mAP@50", "mAP@50-95"]
    values = [precision, recall, map50, map5095]

    plt.figure(figsize=(7, 4))
    bars = plt.bar(metrics_names, values, color=["#4CAF50", "#FFC107", "#2196F3", "#9C27B0"])
    plt.title("YOLOv8 Weapon Detection Evaluation Metrics")
    plt.ylim(0, 1)
    plt.ylabel("Score")

    # Annotate bar values
    for bar in bars:
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02,
                 f"{bar.get_height():.2f}", ha='center', fontsize=10)

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()
