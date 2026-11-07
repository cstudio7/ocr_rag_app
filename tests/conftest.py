"""Shared pytest setup.

The backend uses flat imports (``from config import ...``), so ``backend/`` is
put on ``sys.path``. Heavy optional dependencies (embedding model, vector DB,
OCR tooling) are replaced with lightweight stubs when they are not installed,
so the unit tests run quickly and offline.
"""
import importlib.util
import os
import sys
import types
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("DATABASE_URL", "sqlite://")  # in-memory


def _installed(top_level):
    if top_level in sys.modules:
        return getattr(sys.modules[top_level], "__spec__", None) is not None
    return importlib.util.find_spec(top_level) is not None


def _stub(name, **attrs):
    if _installed(name.split(".")[0]):
        return
    module = types.ModuleType(name)
    module.__dict__.update(attrs)
    sys.modules[name] = module
    parent, _, child = name.rpartition(".")
    if parent and parent in sys.modules:
        setattr(sys.modules[parent], child, module)


class _FakeSentenceTransformer:
    def __init__(self, *args, **kwargs):
        pass

    def encode(self, texts, **kwargs):
        return [[0.0, 0.0, 0.0] for _ in texts]


_stub("sentence_transformers", SentenceTransformer=_FakeSentenceTransformer)
_stub("chromadb")
_stub("chromadb.utils", embedding_functions=types.SimpleNamespace())
_stub("fitz")
_stub("pdfplumber")
_stub("pytesseract", pytesseract=types.SimpleNamespace(tesseract_cmd=None))
_stub("pdf2image", convert_from_path=lambda *a, **k: [])
