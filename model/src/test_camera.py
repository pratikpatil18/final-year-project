import cv2
from ultralytics import YOLO

def main():
    model = YOLO("models/yolov8n_custom.pt")

    cap = cv2.VideoCapture(0)  # 0 = default laptop webcam
    if not cap.isOpened():
        print("❌ Could not open camera.")
        return

    print("🎥 Starting real-time weapon detection... Press 'q' to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ Failed to grab frame.")
            break

        # Run detection
        results = model(frame)
        annotated_frame = results[0].plot()

        cv2.imshow("AI Ranger - Weapon Detection", annotated_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("🟢 Detection stopped.")

if __name__ == "__main__":
    main()
