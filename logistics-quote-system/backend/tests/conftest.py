# backend/tests/conftest.py
"""Load route_helpers directly from file to avoid FastAPI package init chain."""
import importlib.util
import sys
from pathlib import Path

HELPERS_PATH = Path(__file__).parent.parent / "app" / "api" / "v1" / "route_helpers.py"
spec = importlib.util.spec_from_file_location("route_helpers", HELPERS_PATH)
_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_mod)
sys.modules["route_helpers"] = _mod
