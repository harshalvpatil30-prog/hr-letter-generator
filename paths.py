import os
import sys


def app_dir() -> str:
    """Folder of the .exe when packaged, or of this script when developing."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def app_path(*parts) -> str:
    return os.path.join(app_dir(), *parts)