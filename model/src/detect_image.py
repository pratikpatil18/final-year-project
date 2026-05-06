from ultralytics import YOLO
import cv2

def main():
    model = YOLO("models/yolov8n_custom.pt")
#  "E:\Test Project\sample1.jpg"
    image_path = "E:\Test Project\images.jpg"  # put test image path here
    results = model(image_path)
    results[0].show()  # show output window
    results[0].save(filename="runs/detect/sample_result.jpg")

    print("✅ Detection complete. Saved result to runs/detect/sample_result.jpg")

if __name__ == "__main__":
    main()
