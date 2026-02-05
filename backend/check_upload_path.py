import os
import sys

# Add current directory to path so we can import app
sys.path.append(os.getcwd())

from app.config import settings

def check_paths():
    print(f"Current Working Directory: {os.getcwd()}")
    upload_dir = settings.file_storage.upload_dir
    print(f"Configured Upload Dir: {upload_dir}")
    abs_path = os.path.abspath(upload_dir)
    print(f"Absolute Upload Path: {abs_path}")
    
    if os.path.exists(abs_path):
        print(f"Upload directory exists.")
    else:
        print(f"Upload directory does NOT exist.")
        try:
            os.makedirs(abs_path, exist_ok=True)
            print(f"Successfully created upload directory.")
        except Exception as e:
            print(f"Failed to create upload directory: {e}")

if __name__ == "__main__":
    check_paths()
