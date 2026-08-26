"""Popup automatico al seleccionar texto con el raton.

Windows no notifica "el usuario ha seleccionado texto" a otras aplicaciones.
El unico metodo que funciona en cualquier programa es detectar el gesto:
boton izquierdo pulsado -> arrastre -> soltado. Ahi se sintetiza Ctrl+C y se
mira que hay.

Como eso toca el portapapeles del usuario, todo el fichero esta construido
alrededor de NO dispararse de mas.
"""

from __future__ import annotations

import threading
import time

from app.config import (
    AUTO_POPUP_DEBOUNCE_S,
    AUTO_POPUP_MIN_CHARS,
    AUTO_POPUP_MIN_DRAG_PX,
    AUTO_POPUP_MIN_WORDS,
    AUTO_POPUP_ONLY_ENGLISH,
)
from app.log import setup as _setup

log = _setup().getChild("watcher")

_enabled = True
_lock = threading.Lock()
_last_fire = 0.0
_last_text = ""
_press: tuple[int, int, float] | None = None


def set_enabled(value: bool) -> None:
    global _enabled
    _enabled = value
    log.info("popup automatico: %s", "ON" if value else "OFF")


def is_enabled() -> bool:
    return _enabled


def _worth_translating(text: str) -> bool:
    """Filtros baratos antes de gastar en traducir."""
    t = text.strip()
    if len(t) < AUTO_POPUP_MIN_CHARS:
        return False
    if len(t.split()) < AUTO_POPUP_MIN_WORDS:
        return False
    if t == _last_text:            # el usuario reselecciona lo mismo
        return False
    return True


def _handle_selection() -> None:
    """Se ejecuta en un hilo: lee la seleccion y decide si mostrar el popup."""
    global _last_text

    from app import popup, selection
    from app.translator import detect_lang, translate

    text = selection.read_selection()
    if not text.strip():
        selection.restore_clipboard()
        return

    if not _worth_translating(text):
        log.debug("descartado por filtros (%d chars)", len(text.strip()))
        selection.restore_clipboard()
        return

    lang = detect_lang(text)
    if AUTO_POPUP_ONLY_ENGLISH and lang != "en":
        log.debug("descartado: idioma detectado %s", lang)
        selection.restore_clipboard()
        return

    _last_text = text.strip()
    log.info("auto-popup: traduciendo %s->es (%d chars)", lang, len(text))

    result = translate(text, lang, "es")
    selection.restore_clipboard()
    popup.show(result, "Traduccion automatica EN -> ES")


def _on_click(x: int, y: int, button, pressed: bool) -> None:
    global _press, _last_fire

    from pynput import mouse
    if button != mouse.Button.left:
        return

    now = time.time()

    if pressed:
        _press = (x, y, now)
        return

    if _press is None:
        return
    px, py, pt = _press
    _press = None

    if not _enabled:
        return

    # Un clic simple no es una seleccion: exigimos arrastre.
    if abs(x - px) < AUTO_POPUP_MIN_DRAG_PX and abs(y - py) < AUTO_POPUP_MIN_DRAG_PX:
        return

    if now - _last_fire < AUTO_POPUP_DEBOUNCE_S:
        return

    # Si ya hay una traduccion en curso, no encolamos otra.
    if not _lock.acquire(blocking=False):
        return
    _last_fire = now

    def work() -> None:
        try:
            # Margen para que la app destino asiente la seleccion antes del Ctrl+C.
            time.sleep(0.12)
            _handle_selection()
        except Exception as exc:
            log.error("auto-popup fallo: %s", exc, exc_info=True)
        finally:
            _lock.release()

    threading.Thread(target=work, daemon=True).start()


def start():
    """Arranca el listener de raton. Devuelve el listener o None si falla."""
    try:
        from pynput import mouse
        listener = mouse.Listener(on_click=_on_click)
        listener.start()
        log.info("listener de raton ACTIVO (popup automatico)")
        return listener
    except Exception as exc:
        log.error("no se pudo arrancar el listener de raton: %s", exc, exc_info=True)
        return None
