"""Log a fichero.

La app se compila con console=False: sin esto, cualquier excepcion al
arrancar la mata en silencio y no queda ni rastro de por que.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path


def log_path() -> Path:
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    d = Path(base) / "traslatetool"
    d.mkdir(parents=True, exist_ok=True)
    return d / "traslatetool.log"


def setup() -> logging.Logger:
    p = log_path()
    handlers: list[logging.Handler] = [logging.FileHandler(p, encoding="utf-8")]
    if sys.stdout is not None:            # build de consola
        handlers.append(logging.StreamHandler(sys.stdout))

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)-7s %(name)-12s %(message)s",
        handlers=handlers,
        force=True,
    )
    log = logging.getLogger("traslatetool")
    log.info("=" * 60)
    log.info("arranque | python=%s | frozen=%s", sys.version.split()[0],
             getattr(sys, "frozen", False))
    log.info("log en %s", p)
    return log
