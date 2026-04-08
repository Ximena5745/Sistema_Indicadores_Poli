import importlib.util
import sys
from pathlib import Path


def load_disabled_page(page_filename: str):
    root = Path(__file__).resolve().parents[2]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    source_path = root / "pages_disabled" / page_filename
    spec = importlib.util.spec_from_file_location(page_filename.replace(".py", ""), source_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
