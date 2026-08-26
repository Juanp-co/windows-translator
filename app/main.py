"""Punto de entrada: icono de bandeja + atajos globales."""

from __future__ import annotations

import sys
import threading
import traceback

from app.log import setup as setup_log, log_path

log = setup_log()

_busy = threading.Lock()


def _run(fn, nombre: str) -> None:
    """Ejecuta `fn` en un hilo, ignorando disparos mientras uno esta en curso."""
    log.info("atajo disparado: %s", nombre)

    def wrapper() -> None:
        from app import popup
        if not _busy.acquire(blocking=False):
            log.warning("%s ignorado: hay otro en curso", nombre)
            return
        try:
            fn()
        except Exception as exc:
            log.error("%s fallo: %s", nombre, exc)
            log.error(traceback.format_exc())
            try:
                popup.show(f"{type(exc).__name__}: {exc}", "Error")
            except Exception:
                pass
        finally:
            _busy.release()

    threading.Thread(target=wrapper, daemon=True).start()


def on_popup() -> None:
    """Ctrl+Alt+R - traduce la seleccion y la muestra en un popup."""
    from app import popup, selection
    from app.translator import detect_lang, translate

    text = selection.read_selection()
    log.info("seleccion leida: %d caracteres", len(text))
    if not text.strip():
        popup.show("No hay texto seleccionado.", "traslatetool")
        return

    src = detect_lang(text)
    tgt = "es" if src == "en" else "en"
    log.info("traduciendo %s->%s", src, tgt)
    result = translate(text, src, tgt)
    log.info("traduccion lista: %d caracteres", len(result))

    selection.restore_clipboard()
    popup.show(result, f"Traduccion {src.upper()} -> {tgt.upper()}")


def on_replace() -> None:
    """Ctrl+Alt+Y - traduce la seleccion y la escribe encima."""
    from app import popup, selection
    from app.translator import detect_lang, translate

    text = selection.read_selection()
    log.info("seleccion leida: %d caracteres", len(text))
    if not text.strip():
        popup.show("No hay texto seleccionado.", "traslatetool")
        return

    src = detect_lang(text)
    tgt = "en" if src == "es" else "es"
    log.info("traduciendo %s->%s", src, tgt)
    result = translate(text, src, tgt)
    selection.replace_selection(result)
    log.info("reemplazo hecho")


def _icon_image():
    from PIL import Image, ImageDraw
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((2, 2, 62, 62), fill=(37, 99, 235, 255))
    d.text((26, 22), "T", fill="white")
    return img


def main() -> int:
    from app import popup
    from app.config import HOTKEY_POPUP, HOTKEY_REPLACE

    log.info("atajos configurados: popup=%s replace=%s", HOTKEY_POPUP, HOTKEY_REPLACE)

    # --- atajos globales ----------------------------------------------------
    try:
        from pynput import keyboard
        hotkeys = keyboard.GlobalHotKeys({
            HOTKEY_POPUP: lambda: _run(on_popup, "popup"),
            HOTKEY_REPLACE: lambda: _run(on_replace, "replace"),
        })
        hotkeys.start()
        log.info("listener de atajos ACTIVO")
    except Exception:
        log.critical("no se pudieron registrar los atajos")
        log.critical(traceback.format_exc())
        return 2

    # --- popup automatico al seleccionar con el raton ------------------------
    from app import watcher
    from app.config import AUTO_POPUP
    watcher.set_enabled(AUTO_POPUP)
    mouse_listener = watcher.start() if AUTO_POPUP else None

    # --- icono de bandeja ---------------------------------------------------
    # No es critico: si falla, la app sigue con los atajos funcionando.
    icon = None
    try:
        import pystray
        def quit_app(ic, _item) -> None:
            log.info("salida solicitada desde la bandeja")
            ic.stop()
            hotkeys.stop()
            if mouse_listener is not None:
                mouse_listener.stop()
            popup.stop_loop()

        def toggle_auto(ic, item) -> None:
            watcher.set_enabled(not watcher.is_enabled())
            ic.update_menu()

        icon = pystray.Icon(
            "traslatetool", _icon_image(),
            f"traslatetool | {HOTKEY_POPUP} popup | {HOTKEY_REPLACE} reemplazar",
            menu=pystray.Menu(
                pystray.MenuItem(
                    "Popup automatico al seleccionar",
                    toggle_auto,
                    checked=lambda _i: watcher.is_enabled(),
                ),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Traducir seleccion (popup)", lambda: _run(on_popup, "popup")),
                pystray.MenuItem("Reemplazar seleccion", lambda: _run(on_replace, "replace")),
                pystray.MenuItem("Ver log", lambda: __import__("os").startfile(log_path())),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Salir", quit_app),
            ),
        )
        threading.Thread(target=icon.run, daemon=True).start()
        log.info("icono de bandeja lanzado")
    except Exception:
        log.error("fallo el icono de bandeja (los atajos siguen activos)")
        log.error(traceback.format_exc())

    # --- bucle de tkinter (hilo principal) ----------------------------------
    try:
        log.info("arrancando bucle de tkinter")
        popup.start_loop()
    except Exception:
        log.critical("fallo el bucle de tkinter")
        log.critical(traceback.format_exc())
        return 3

    log.info("salida limpia")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        log.critical("excepcion no capturada:\n%s", traceback.format_exc())
        sys.exit(1)
