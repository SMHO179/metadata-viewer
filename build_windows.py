import subprocess
import sys
import os
import shutil

def build():
    print("🚀 Starting Metadata Viewer Build Process...")
    
    # 1. Install dependencies
    print("📦 Installing requirements...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # 2. Run PyInstaller
    print("🔨 Building executable...")
    # Use the spec file
    subprocess.check_call(["pyinstaller", "--noconfirm", "metadata_viewer.spec"])

    print("\n✅ Build Complete!")
    print(f"📁 Output directory: {os.path.abspath('dist/MetadataViewer')}")

if __name__ == "__main__":
    build()
