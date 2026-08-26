"""Punto de entrada: icono de bandeja + atajos globales."""

from __future__ import annotations

import sys
import threading

from PIL import Image, ImageDraw
from pynput import keyboard

from app import popup, selection
from app.config import HOTKEY_POPUP, HOTKEY_REPLACE
from app.translator import detect_lang, translate

_busy = threading.Lock()


def _run(fn) -> None:
    """Ejecuta `fn` en un hilo, ignorando disparos mientras uno está en curso."""
    def wrapper() -> None:
        if not _busy.acquire(blocking=False):
            return
        try:
            fn()
        except Exception as exc:  # nunca dejamos morir el hilo del atajo
            popup.show(f"{type(exc).__name__}: {exc}", "Error")
        finally:
            _busy.release()

    threading.Thread(target=wrapper, daemon=True).start()


def on_popup() -> None:
    """Ctrl+Alt+R — traduce la selección al español y la muestra."""
    text = selection.read_selection()
    if not text.strip():
        popup.show("No hay texto seleccionado.", "traslatetool")
        return

    src = detect_lang(text)
    tgt = "es" if src == "en" else "en"
    result = translate(text, src, tgt)

    selection.restore_clipboard()
    popup.show(result, f"Traducción {src.upper()} → {tgt.upper()}")


def on_replace() -> None:
    """Ctrl+Alt+E — traduce la selección al inglés y la escribe encima."""
    text = selection.read_selection()
    if not text.strip():
        popup.show("No hay texto seleccionado.", "traslatetool")
        return

    src = detect_lang(text)
    tgt = "en" if src == "es" else "es"
    result = translate(text, src, tgt)
    selection.replace_selection(result)


def _icon_image() -> Image.Image:
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((2, 2, 62, 62), fill=(37, 99, 235, 255))
    d.text((20, 18), "T", fill="white")
    return img


def main() -> int:
    import pystray

    hotkeys = keyboard.GlobalHotKeys({
        HOTKEY_POPUP: lambda: _run(on_popup),
        HOTKEY_REPLACE: lambda: _run(on_replace),
    })
    hotkeys.start()

    def quit_app(icon, _item) -> None:
        icon.stop()
        hotkeys.stop()
        popup.stop_loop()

    icon = pystray.Icon(
        "traslatetool",
        _icon_image(),
        "traslatetool  ·  Ctrl+Alt+R popup  ·  Ctrl+Alt+E reemplazar",
        menu=pystray.Menu(
            pystray.MenuItem("Traducir selección (popup)", lambda: _run(on_popup)),
            pystray.MenuItem("Reemplazar selección", lambda: _run(on_replace)),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Salir", quit_app),
        ),
    )
    threading.Thread(target=icon.run, daemon=True).start()

    popup.start_loop()  # bloquea hasta que se sale
    return 0


if __name__ == "__main__":
    sys.exit(main())
