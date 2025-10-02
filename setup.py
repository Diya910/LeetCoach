#!/usr/bin/env python3
"""
LeetCoach Setup Script
Helps set up the LeetCoach application
"""

import os
import sys
import shutil
from pathlib import Path

def main():
    """Set up LeetCoach application."""
    
    print("🧠 LeetCoach Setup")
    print("=" * 30)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8+ is required!")
        print(f"   Current version: {sys.version}")
        sys.exit(1)
    
    print(f"✅ Python version: {sys.version.split()[0]}")
    
    # Create .env file if it doesn't exist
    backend_dir = Path(__file__).parent / "backend"
    env_file = backend_dir / ".env"
    env_example = backend_dir / "env.example"
    
    if not env_file.exists() and env_example.exists():
        print("📝 Creating .env file from template...")
        shutil.copy(env_example, env_file)
        print("   Please edit backend/.env with your API keys")
    elif env_file.exists():
        print("✅ .env file already exists")
    else:
        print("⚠️  No .env template found")
    
    # Install backend dependencies
    print("📦 Installing backend dependencies...")
    try:
        import subprocess
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", 
            str(backend_dir / "app" / "requirements.txt")
        ], check=True)
        print("✅ Backend dependencies installed")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        sys.exit(1)
    
    # Check Chrome extension
    extension_dir = Path(__file__).parent / "chrome_extension"
    if extension_dir.exists():
        print("✅ Chrome extension files found")
    else:
        print("❌ Chrome extension directory not found!")
        sys.exit(1)
    
    print("\n🎉 Setup complete!")
    print("\nNext steps:")
    print("1. Edit backend/.env with your API keys")
    print("2. Run: python start_backend.py")
    print("3. Load the Chrome extension from chrome_extension/ folder")
    print("4. Visit a LeetCode problem page to test!")
    
    print("\nFor detailed instructions, see README.md")

if __name__ == "__main__":
    main()
