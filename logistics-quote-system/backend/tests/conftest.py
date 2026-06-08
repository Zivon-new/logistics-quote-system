# backend/tests/conftest.py
"""Load pure-utility modules directly from file to avoid FastAPI package init chain."""
import importlib.util
import sys
from pathlib import Path

APP_DIR = Path(__file__).parent.parent / "app"


def _load_from_file(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    sys.modules[module_name] = mod


_load_from_file("route_helpers", APP_DIR / "services" / "route_helpers.py")
_load_from_file("fee_service", APP_DIR / "services" / "fee_service.py")
