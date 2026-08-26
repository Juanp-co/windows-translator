"""Leer la selección actual y, opcionalmente, reemplazarla.

Windows no expone "el texto seleccionado" a otras apps. El único método que
funciona en cualquier programa es sintetizar Ctrl+C / Ctrl+V, guardando y
restaurando el portapapeles del usuario para no pisárselo.
"""

from __future__ import annotations

import time

import pyperclip
from pynput.keyboard import Controller, Key

from app.config import COPY_WAIT_S, PASTE_WAIT_S

_kb = Controller()


def _tap(key: str) -> None:
    """Envía Ctrl+<key>."""
    with _kb.pressed(Key.ctrl):
        _kb.press(key)
        _kb.release(key)


def _release_modifiers() -> None:
    """Suelta Ctrl y Alt.

    El atajo se dispara con las teclas físicamente pulsadas. Si enviamos Ctrl+C
    sin soltarlas antes, Windows recibe Ctrl+Alt+C y la copia no ocurre.
    """
    for key in (Key.alt_l, Key.alt_r, Key.ctrl_l, Key.ctrl_r):
        try:
            _kb.release(key)
        except Exception:
            pass
    time.sleep(0.05)


def read_selection() -> str:
    """Copia la selección y devuelve su texto. Restaura el portapapeles."""
    _release_modifiers()

    try:
        saved = pyperclip.paste()
    except Exception:
        saved = ""

    pyperclip.copy("")
    _tap("c")
    time.sleep(COPY_WAIT_S)

    text = pyperclip.paste()

    # Restauramos solo si no obtuvimos nada; si hay texto, el llamador puede
    # necesitar el portapapeles todavía y restaura al terminar.
    if not text:
        pyperclip.copy(saved)
        return ""

    _restore_pending.append(saved)
    return text


_restore_pending: list[str] = []


def restore_clipboard() -> None:
    """Devuelve al portapapeles lo que hubiera antes de la última lectura."""
    if _restore_pending:
        try:
            pyperclip.copy(_restore_pending.pop())
        except Exception:
            pass


def replace_selection(new_text: str) -> None:
    """Sustituye la selección actual por `new_text` mediante Ctrl+V."""
    pyperclip.copy(new_text)
    time.sleep(0.05)
    _tap("v")
    time.sleep(PASTE_WAIT_S)
    restore_clipboard()
