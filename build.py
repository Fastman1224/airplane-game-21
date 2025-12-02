#!/usr/bin/env python
"""
اسکریپت ساخت برای C++ acceleration module
برای Windows: python build.py
برای Linux/Mac: python build.py
"""

import os
import sys
import subprocess
import platform

def build_extension():
    """کامپایل کردن C++ extension"""
    print("=" * 60)
    print("🔨 Building C++ Acceleration Module...")
    print("=" * 60)
    
    # پاک کردن build directory قدیمی
    if os.path.exists("build"):
        print("Cleaning old build directory...")
        subprocess.run([sys.executable, "setup.py", "clean", "--all"], 
                      capture_output=True)
    
    # کامپایل
    print("\nCompiling C++ code...")
    result = subprocess.run([sys.executable, "setup.py", "build_ext", "--inplace"],
                          capture_output=False)
    
    if result.returncode == 0:
        print("\n" + "=" * 60)
        print("✅ Build successful!")
        print("=" * 60)
        print("\nThe game_accelerator module is now available.")
        print("Run: python airplane.py")
        return True
    else:
        print("\n" + "=" * 60)
        print("⚠️  C++ Build failed - Using Python Fallback")
        print("=" * 60)
        print("\nThe game will run with Python acceleration (fallback mode).")
        print("Performance will still be good for most systems.")
        print("\nTo enable full C++ acceleration, install:")
        print("  Windows: Visual C++ Build Tools")
        print("    https://visualstudio.microsoft.com/visual-cpp-build-tools/")
        print("\n  Linux: sudo apt install build-essential python3-dev")
        print("  macOS: xcode-select --install")
        return True  # Return True because fallback is available

def check_requirements():
    """بررسی requirement‌ها"""
    print("Checking requirements...")
    
    required = ['pybind11', 'setuptools']
    missing = []
    
    for package in required:
        try:
            __import__(package)
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ✗ {package}")
            missing.append(package)
    
    if missing:
        print(f"\nInstalling missing packages: {', '.join(missing)}")
        subprocess.run([sys.executable, "-m", "pip", "install"] + missing)
    
    return True  # Always return True because fallback works

def main():
    print("\n🎮 Game Accelerator Build Script")
    print(f"Platform: {platform.system()}")
    print(f"Python: {sys.version}\n")
    
    check_requirements()
    build_extension()
    
    print("\n" + "=" * 60)
    print("✅ Ready to play!")
    print("=" * 60)
    print("\nRun the game with: python airplane.py")
    print("\nNote: Python fallback acceleration is always available.")
    print("Performance is optimized for most modern systems.")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
