"""Descarga los modelos Argos en<->es y los deja listos para CTranslate2.

Un fichero .argosmodel es un ZIP que contiene un modelo CTranslate2 y un modelo
SentencePiece. Los extraemos y aplanamos para poder cargarlos directamente,
sin la librería argostranslate (que arrastraría stanza -> PyTorch).

    python scripts/fetch_models.py

Si una URL da 404, mira el índice y ajusta PAIRS:
    https://raw.githubusercontent.com/argosopentech/argospm-index/main/index.json
"""

from __future__ import annotations

import io
import json
import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODELS = ROOT / "models"
INDEX_URL = "https://raw.githubusercontent.com/argosopentech/argospm-index/main/index.json"

# Versiones FIJADAS a propósito, no las últimas del índice.
#
# El paquete es_en-1_9 usa BPE de subword-nmt en vez de SentencePiece (su
# bpe.model es texto plano, no un ModelProto) y además pesa 285 MB. La 1_0
# usa SentencePiece, igual que en_es, y pesa 87 MB. Mantener las dos
# direcciones con el mismo tokenizador evita una dependencia extra.
#
# Antes de subir de versión, comprueba el formato:
#   head -c 16 models/<par>/sentencepiece.model | xxd
#   ModelProto empieza por 0a 0e ...;  BPE empieza por "#version:"
PINNED = {
    ("en", "es"): "translate-en_es-1_0.argosmodel",
    ("es", "en"): "translate-es_en-1_0.argosmodel",
}
PAIRS = list(PINNED)

# argos-net.com devuelve 403 sin User-Agent de navegador.
UA = {"User-Agent": "Mozilla/5.0 (compatible; traslatetool/0.1)"}

# Si un mirror cae, probamos el siguiente reescribiendo el prefijo de la URL.
MIRRORS = [
    "https://argos-net.com/v1/",
    "https://data.argosopentech.com/argospm/v1/",
]


def _get(url: str, timeout: int = 600) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def load_index() -> list[dict]:
    print(f"Índice: {INDEX_URL}")
    return json.loads(_get(INDEX_URL, timeout=60).decode("utf-8"))


def find_urls(src: str, tgt: str) -> list[str]:
    """URLs candidatas del paquete fijado, una por mirror."""
    filename = PINNED[(src, tgt)]
    return [mirror + filename for mirror in MIRRORS]


def download(urls: list[str]) -> bytes:
    last: Exception | None = None
    for url in urls:
        try:
            print(f"  ↓ {url}")
            return _get(url)
        except Exception as exc:
            print(f"    falló: {exc}")
            last = exc
    raise SystemExit(f"Ningún mirror respondió. Último error: {last}")


def flatten(zf: zipfile.ZipFile, dest: Path) -> None:
    """Extrae model/* y el modelo SentencePiece a `dest`, sin jerarquía.

    Se ignora deliberadamente todo lo que cuelga de stanza/: es un modelo
    PyTorch para partir frases (el .pt es la mayor parte del peso del paquete)
    y aquí lo sustituye el regex de translator.py.

    El fichero SentencePiece se llama `bpe.model` en unos paquetes y
    `sentencepiece.model` en otros; lo normalizamos a `sentencepiece.model`.
    """
    dest.mkdir(parents=True, exist_ok=True)
    wanted_model_files = {"model.bin", "shared_vocabulary.txt", "shared_vocabulary.json",
                          "config.json", "vocabulary.txt", "vocabulary.json",
                          "source_vocabulary.txt", "target_vocabulary.txt",
                          "source_vocabulary.json", "target_vocabulary.json"}

    found_sp = False
    found_bin = False

    for info in zf.infolist():
        if info.is_dir():
            continue
        parts = Path(info.filename).parts
        name = Path(info.filename).name

        if "stanza" in parts:          # PyTorch: fuera
            continue

        is_model = "model" in parts and name in wanted_model_files
        is_sp = name in ("bpe.model", "sentencepiece.model", "spm.model") \
            or (name.endswith(".model") and "sentencepiece" in name)

        if not (is_model or is_sp):
            continue

        out = dest / ("sentencepiece.model" if is_sp else name)
        with zf.open(info) as src_f, open(out, "wb") as dst_f:
            shutil.copyfileobj(src_f, dst_f)

        found_sp |= is_sp
        found_bin |= name == "model.bin"

    if not found_bin:
        raise SystemExit("El paquete no traía model.bin. Contenido:\n"
                         + "\n".join(zf.namelist()[:40]))
    if not found_sp:
        raise SystemExit("El paquete no traía modelo SentencePiece. Contenido:\n"
                         + "\n".join(zf.namelist()[:40]))


def verify(dest: Path) -> None:
    """Falla pronto si el SentencePiece no es un ModelProto binario."""
    head = (dest / "sentencepiece.model").read_bytes()[:16]
    if head.startswith(b"#version:"):
        raise SystemExit(
            f"{dest.name}: el paquete trae BPE de subword-nmt, no SentencePiece.\n"
            "Fija otra versión en PINNED."
        )


def main() -> int:
    MODELS.mkdir(exist_ok=True)

    for src, tgt in PAIRS:
        dest = MODELS / f"{src}_{tgt}"
        if (dest / "model.bin").exists():
            print(f"✓ {src}->{tgt} ya está en {dest}")
            continue

        print(f"↓ {src}->{tgt}")
        blob = download(find_urls(src, tgt))
        print(f"  {len(blob) / 1_000_000:.0f} MB descargados, extrayendo…")

        with zipfile.ZipFile(io.BytesIO(blob)) as zf:
            flatten(zf, dest)
        verify(dest)
        print(f"✓ {dest}")

    total = sum(f.stat().st_size for f in MODELS.rglob("*") if f.is_file())
    print(f"\nTotal en disco: {total / 1_000_000:.0f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
