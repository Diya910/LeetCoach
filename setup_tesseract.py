#!/usr/bin/env python3
"""
Setup script for Tesseract OCR on Windows.
This script helps install and configure Tesseract for LeetCoach.
"""

import os
import sys
import platform
import subprocess
import urllib.request
import zipfile
import shutil
from pathlib import Path

def check_tesseract_installed():
    """Check if Tesseract is already installed and accessible."""
    try:
        result = subprocess.run(['tesseract', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ Tesseract is already installed and working!")
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    return False

def download_tesseract_windows():
    """Download and install Tesseract for Windows."""
    print("📥 Downloading Tesseract for Windows...")
    
    # Tesseract download URL (latest stable)
    url = "https://github.com/UB-Mannheim/tesseract/releases/download/v5.3.3.20231005/tesseract-ocr-w64-setup-5.3.3.20231005.exe"
    
    installer_path = "tesseract-installer.exe"
    
    try:
        print("Downloading installer...")
        urllib.request.urlretrieve(url, installer_path)
        print(f"✅ Downloaded installer to {installer_path}")
        print("\n🔧 Please run the installer manually:")
        print(f"   {os.path.abspath(installer_path)}")
        print("\n📝 During installation, note the installation path (usually C:\\Program Files\\Tesseract-OCR\\)")
        print("   You'll need this path to configure the extension.")
        
        return True
    except Exception as e:
        print(f"❌ Failed to download Tesseract: {e}")
        return False

def setup_tesseract_path():
    """Help user configure Tesseract path."""
    print("\n🔧 Tesseract Path Configuration")
    print("=" * 50)
    
    common_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        r"C:\Users\{}\AppData\Local\Tesseract-OCR\tesseract.exe".format(os.getenv('USERNAME', '')),
    ]
    
    print("Checking common installation paths...")
    for path in common_paths:
        if os.path.exists(path):
            print(f"✅ Found Tesseract at: {path}")
            return path
    
    print("❌ Tesseract not found in common locations.")
    print("\nPlease provide the path to tesseract.exe:")
    user_path = input("Tesseract path: ").strip()
    
    if user_path and os.path.exists(user_path):
        print(f"✅ Tesseract found at: {user_path}")
        return user_path
    else:
        print("❌ Invalid path provided.")
        return None

def install_python_dependencies():
    """Install required Python packages."""
    print("\n📦 Installing Python dependencies...")
    
    packages = [
        "pytesseract",
        "opencv-python",
        "Pillow"
    ]
    
    for package in packages:
        try:
            print(f"Installing {package}...")
            subprocess.run([sys.executable, "-m", "pip", "install", package], 
                         check=True, capture_output=True)
            print(f"✅ {package} installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {package}: {e}")

def main():
    """Main setup function."""
    print("🧠 LeetCoach Tesseract Setup")
    print("=" * 40)
    
    if platform.system() != "Windows":
        print("❌ This setup script is designed for Windows.")
        print("   For other platforms, please install Tesseract manually:")
        print("   - Ubuntu/Debian: sudo apt-get install tesseract-ocr")
        print("   - macOS: brew install tesseract")
        print("   - Arch: sudo pacman -S tesseract")
        return
    
    # Check if already installed
    if check_tesseract_installed():
        print("🎉 Tesseract is ready to use!")
        return
    
    # Download and install
    if not download_tesseract_windows():
        print("❌ Setup failed. Please install Tesseract manually.")
        return
    
    # Install Python dependencies
    install_python_dependencies()
    
    # Configure path
    tesseract_path = setup_tesseract_path()
    
    if tesseract_path:
        print(f"\n🎉 Setup complete!")
        print(f"Tesseract path: {tesseract_path}")
        print("\nNext steps:")
        print("1. Make sure your .env file has the correct API keys")
        print("2. Restart the LeetCoach backend")
        print("3. Test the extension on a LeetCode problem page")
    else:
        print("\n❌ Setup incomplete. Please install Tesseract manually and configure the path.")

if __name__ == "__main__":
    main()
