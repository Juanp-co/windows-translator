"""Traducción con CTranslate2 + SentencePiece.

Los modelos se cargan de forma perezosa: la app arranca en ~60 MB y solo sube
cuando traduces por primera vez en esa dirección.
"""

from __future__ import annotations

import re
import threading

from app.config import BEAM_SIZE, COMPUTE_TYPE, MAX_INPUT_CHARS, MODEL_DIRS

# ctranslate2 y sentencepiece se importan dentro de _load(): así este módulo
# es importable sin ellos (útil para probar detect_lang en macOS) y la app
# arranca sin pagar el coste de cargar las librerías nativas.
_cache: dict = {}
_lock = threading.Lock()


def _load(src: str, tgt: str):
    """Carga (y memoiza) el par de modelos para una dirección."""
    import ctranslate2
    import sentencepiece as spm

    key = (src, tgt)
    with _lock:
        if key in _cache:
            return _cache[key]

        directory = MODEL_DIRS.get(key)
        if directory is None:
            raise ValueError(f"Dirección no soportada: {src}->{tgt}")
        if not directory.is_dir():
            raise FileNotFoundError(
                f"Faltan los modelos en {directory}. Ejecuta scripts/fetch_models.py"
            )

        translator = ctranslate2.Translator(str(directory), compute_type=COMPUTE_TYPE)
        sp = spm.SentencePieceProcessor()
        sp.load(str(directory / "sentencepiece.model"))

        _cache[key] = (translator, sp)
        return _cache[key]


# Corta en frases por puntuación final seguida de espacio. Suficiente para
# párrafos cortos; sustituye a `stanza`, que arrastraría PyTorch.
_SENTENCE_RE = re.compile(r"(?<=[.!?…])\s+")


def _split_sentences(text: str) -> list[str]:
    parts: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        parts.extend(s for s in _SENTENCE_RE.split(line) if s)
    return parts or [text.strip()]


def translate(text: str, src: str, tgt: str) -> str:
    """Traduce `text` de `src` a `tgt`. Devuelve el texto traducido."""
    text = text.strip()
    if not text:
        return ""
    if len(text) > MAX_INPUT_CHARS:
        text = text[:MAX_INPUT_CHARS]

    translator, sp = _load(src, tgt)

    sentences = _split_sentences(text)
    tokenized = [sp.encode(s, out_type=str) for s in sentences]

    results = translator.translate_batch(
        tokenized,
        beam_size=BEAM_SIZE,
        max_batch_size=8,
    )

    out = [sp.decode(r.hypotheses[0]) for r in results]
    return " ".join(out)


# --- Detección de idioma ----------------------------------------------------
# Heurística deliberadamente simple: solo hay que distinguir ES de EN, y evitamos
# una dependencia más en el bundle. Se puede cambiar por `langdetect` si hace falta.

_ES_CHARS = set("ñáéíóúü¿¡Ñ")
_ES_WORDS = {
    "el", "la", "los", "las", "de", "que", "y", "en", "un", "una", "por", "con",
    "para", "es", "se", "no", "su", "al", "lo", "como", "más", "pero", "sus",
    "le", "ya", "o", "este", "sí", "porque", "esta", "entre", "cuando", "muy",
    "sin", "sobre", "también", "me", "hasta", "hay", "donde", "quien", "desde",
}
_EN_WORDS = {
    "the", "of", "and", "to", "in", "is", "it", "you", "that", "was", "for",
    "on", "are", "with", "as", "his", "they", "be", "at", "this", "have",
    "from", "or", "had", "by", "but", "not", "what", "were", "we", "when",
    "your", "can", "there", "an", "which", "their", "if", "will", "about",
}


def detect_lang(text: str) -> str:
    """Devuelve 'es' o 'en'. Ante el empate, asume inglés."""
    if any(c in _ES_CHARS for c in text):
        return "es"

    words = re.findall(r"[a-záéíóúñü]+", text.lower())
    if not words:
        return "en"

    es_hits = sum(1 for w in words if w in _ES_WORDS)
    en_hits = sum(1 for w in words if w in _EN_WORDS)
    return "es" if es_hits > en_hits else "en"
