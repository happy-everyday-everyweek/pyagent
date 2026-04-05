import platform
import sys
import os


class PlatformDetector:
    @staticmethod
    def detect() -> str:
        if PlatformDetector.is_mobile():
            return "mobile"
        elif PlatformDetector.is_web():
            return "web"
        else:
            return "desktop"

    @staticmethod
    def is_mobile() -> bool:
        if "ANDROID_ARGUMENT" in os.environ:
            return True
        if "ANDROID_ROOT" in os.environ:
            return True
        if platform.system().lower() == "android":
            return True
        if hasattr(sys, "getandroidapilevel"):
            return True
        if "ios" in platform.platform().lower():
            return True
        if "iphone" in platform.platform().lower():
            return True
        return False

    @staticmethod
    def is_web() -> bool:
        if "PYODIDE" in os.environ:
            return True
        if "BROWSER" in os.environ:
            return True
        if hasattr(sys, "_emscripten_info"):
            return True
        try:
            import js
            return True
        except ImportError:
            return False

    @staticmethod
    def is_desktop() -> bool:
        return not PlatformDetector.is_mobile() and not PlatformDetector.is_web()

    @staticmethod
    def get_os() -> str:
        if PlatformDetector.is_web():
            return "web"
        
        system = platform.system().lower()
        
        if system == "windows":
            return "windows"
        elif system == "darwin":
            return "macos"
        elif system == "linux":
            if PlatformDetector.is_mobile():
                if "android" in platform.platform().lower():
                    return "android"
                return "linux"
            return "linux"
        elif system == "android":
            return "android"
        elif "ios" in platform.platform().lower() or "iphone" in platform.platform().lower():
            return "ios"
        else:
            return system

    @staticmethod
    def get_device_info() -> dict:
        return {
            "platform": PlatformDetector.detect(),
            "os": PlatformDetector.get_os(),
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "is_mobile": PlatformDetector.is_mobile(),
            "is_web": PlatformDetector.is_web(),
            "is_desktop": PlatformDetector.is_desktop(),
        }
