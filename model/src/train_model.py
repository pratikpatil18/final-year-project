from ultralytics import YOLO

def main():
    """
    Train YOLOv8 model on weapon dataset
    """
    # Load pre-trained YOLOv8n model
    model = YOLO("yolov8n.pt")

    # Train the model
    results = model.train(
        data="data/dataset.yaml",
        epochs=3,        # adjust as needed
        imgsz=320,
        batch=4,
        name="weapon_detector",
        project="runs/train",
        device='cpu'         # GPU=0, CPU='cpu'
    )

    print("\n✅ Training complete!")
    print(f"Best model saved at: {results.save_dir}/weights/best.pt")

if __name__ == "__main__":
    main()
