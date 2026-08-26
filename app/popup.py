"""Popup del resultado. tkinter viene en la stdlib: cero peso extra en el bundle.

Toda la interfaz corre en el hilo principal; los atajos llegan desde hilos de
pynput y encolan trabajo con `root.after`.
"""

from __future__ import annotations

import queue
import tkinter as tk

_queue: "queue.Queue[tuple[str, str]]" = queue.Queue()
_root: tk.Tk | None = None
_window: tk.Toplevel | None = None


def show(text: str, title: str = "Traducción") -> None:
    """Encola un popup. Seguro de llamar desde cualquier hilo."""
    _queue.put((title, text))


def _drain() -> None:
    assert _root is not None
    try:
        while True:
            title, text = _queue.get_nowait()
            _render(title, text)
    except queue.Empty:
        pass
    _root.after(100, _drain)


def _render(title: str, text: str) -> None:
    global _window
    assert _root is not None

    if _window is not None:
        try:
            _window.destroy()
        except tk.TclError:
            pass

    win = tk.Toplevel(_root)
    _window = win
    win.title(title)
    win.attributes("-topmost", True)
    win.configure(padx=14, pady=14)

    box = tk.Text(win, wrap="word", width=58, height=8,
                  font=("Segoe UI", 11), relief="flat",
                  background="#f7f7f7", padx=8, pady=8)
    box.insert("1.0", text)
    box.configure(state="normal")  # editable = seleccionable y copiable
    box.pack(fill="both", expand=True)

    bar = tk.Frame(win)
    bar.pack(fill="x", pady=(10, 0))

    def copy_and_close() -> None:
        win.clipboard_clear()
        win.clipboard_append(text)
        win.destroy()

    tk.Button(bar, text="Copiar", width=12, command=copy_and_close).pack(side="right", padx=(6, 0))
    tk.Button(bar, text="Cerrar", width=12, command=win.destroy).pack(side="right")

    win.bind("<Escape>", lambda _e: win.destroy())
    win.update_idletasks()

    # Centrado horizontal, tercio superior de la pantalla
    w, h = win.winfo_width(), win.winfo_height()
    x = (win.winfo_screenwidth() - w) // 2
    y = (win.winfo_screenheight() - h) // 3
    win.geometry(f"+{x}+{y}")

    win.lift()
    win.focus_force()


def start_loop() -> None:
    """Arranca el bucle de tkinter. Bloquea: llamar desde el hilo principal."""
    global _root
    _root = tk.Tk()
    _root.withdraw()  # la ventana raíz nunca se ve
    _root.after(100, _drain)
    _root.mainloop()


def stop_loop() -> None:
    if _root is not None:
        _root.quit()
