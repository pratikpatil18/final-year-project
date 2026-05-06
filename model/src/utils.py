import os

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"📁 Created directory: {path}")

def list_images(directory):
    return [f for f in os.listdir(directory) if f.endswith(('.jpg', '.png', '.jpeg'))]
