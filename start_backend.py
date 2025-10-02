#!/usr/bin/env python3
"""
LeetCoach Backend Startup Script
Starts the FastAPI backend server with proper configuration
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Start the LeetCoach backend server."""
    
    # Get the backend directory
    backend_dir = Path(__file__).parent / "backend"
    
    if not backend_dir.exists():
        print("Error: Backend directory not found!")
        sys.exit(1)
    
    # Change to backend directory
    os.chdir(backend_dir)
    
    print("🚀 Starting LeetCoach Backend Server...")
    print("=" * 50)
    
    # Check if .env file exists
    env_file = backend_dir / ".env"
    if not env_file.exists():
        print("⚠️  Warning: No .env file found!")
        print("   Please create a .env file with your API keys.")
        print("   See README.md for configuration details.")
        print()
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8+ is required!")
        sys.exit(1)
    
    try:
        # Start the server
        print("📦 Installing dependencies...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "app/requirements.txt"], 
                      check=True, capture_output=True)
        
        print("🔧 Starting FastAPI server...")
        print("   API will be available at: http://localhost:8000")
        print("   API docs will be available at: http://localhost:8000/docs")
        print()
        print("Press Ctrl+C to stop the server")
        print("=" * 50)
        
        # Start uvicorn server
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "app.main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload"
        ])
        
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
