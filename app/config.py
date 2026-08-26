"""Configuración central. Todo lo ajustable vive aquí."""

import sys
from pathlib import Path

# --- Atajos (formato pynput.keyboard.GlobalHotKeys) -------------------------
HOTKEY_POPUP = "<ctrl>+<alt>+r"    # inglés seleccionado -> popup en español
HOTKEY_REPLACE = "<ctrl>+<alt>+y"  # español seleccionado -> reemplaza por inglés

# --- Rutas ------------------------------------------------------------------
def _base_dir() -> Path:
    """Raíz de los datos. PyInstaller descomprime en sys._MEIPASS."""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parent.parent


MODELS_DIR = _base_dir() / "models"
MODEL_DIRS = {
    ("en", "es"): MODELS_DIR / "en_es",
    ("es", "en"): MODELS_DIR / "es_en",
}

# --- Modelo -----------------------------------------------------------------
COMPUTE_TYPE = "int8"   # int8 = menos RAM. "float32" si notas pérdida de calidad.
BEAM_SIZE = 2           # 1 = más rápido, 4 = algo mejor. 2 es buen punto medio.
MAX_INPUT_CHARS = 5000  # corta entradas absurdas antes de tokenizar

# --- Temporizado del portapapeles (Windows) ---------------------------------
# Si tu PC es lento o alguna app tarda en responder al Ctrl+C, sube estos valores.
COPY_WAIT_S = 0.35      # espera tras enviar Ctrl+C
PASTE_WAIT_S = 0.35     # espera tras enviar Ctrl+V, antes de restaurar
