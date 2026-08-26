"""Configuración central. Todo lo ajustable vive aquí."""

import sys
from pathlib import Path

# --- Atajos (formato pynput.keyboard.GlobalHotKeys) -------------------------
HOTKEY_POPUP = "<ctrl>+<alt>+r"    # popup manual (respaldo del modo automático)

# OJO: Ctrl+W significa "cerrar pestaña/ventana" en navegadores, editores y
# el Explorador. pynput NO suprime la pulsación (verificado en su fuente:
# GlobalHotKeys pasa **kwargs a Listener y no activa supresión), así que la
# combinación dispara la traducción Y cierra la pestaña. Si eso molesta,
# "<ctrl>+<alt>+w" se comporta igual y no colisiona con nada.
HOTKEY_REPLACE = "<ctrl>+w"        # español seleccionado -> reemplaza por inglés

# --- Popup automático -------------------------------------------------------
# Con esto activo no hace falta pulsar nada: al soltar el ratón tras arrastrar
# sobre un texto en inglés, sale el popup con la traducción al español.
#
# Implica sintetizar Ctrl+C en cada selección, así que hay salvaguardas para
# que no se dispare a cada momento. Se apaga desde el menú de la bandeja.
AUTO_POPUP = True
AUTO_POPUP_MIN_CHARS = 15     # ignora selecciones cortas (clics, una palabra)
AUTO_POPUP_MIN_WORDS = 3
AUTO_POPUP_ONLY_ENGLISH = True  # solo cuando el texto detectado es inglés
AUTO_POPUP_DEBOUNCE_S = 1.5     # tiempo mínimo entre disparos automáticos
AUTO_POPUP_MIN_DRAG_PX = 12     # por debajo de esto es un clic, no una selección

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
