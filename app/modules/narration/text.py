"""Limpieza de la descripción antes de devolverla a la app (SCRUM-264).

El VLM a veces agrega formato o se extiende. La app locuta el texto tal cual, así que aquí se
quita lo que no se puede oír y se recorta a lo que pide el prompt (2 oraciones, ~30 palabras).
"""

import re

MAX_SENTENCES = 2
MAX_WORDS = 40
MAX_CHARS = 300

_MARKDOWN = re.compile(r"[*_`#>]+")
_LIST_PREFIX = re.compile(r"^\s*(?:[-•]|\d+[.)])\s+", re.MULTILINE)
_SPACES = re.compile(r"\s+")
_SENTENCE_END = re.compile(r"(?<=[.!?…])\s+")
_WRAPPING_QUOTES = "\"'«»“”"


def normalize_description(raw: str) -> str:
    """Devuelve el texto listo para locutar, o una cadena vacía si no queda nada útil."""
    text = _LIST_PREFIX.sub("", raw)
    text = _MARKDOWN.sub("", text)
    text = _SPACES.sub(" ", text).strip().strip(_WRAPPING_QUOTES).strip()
    if not text:
        return ""

    sentences = _SENTENCE_END.split(text)[:MAX_SENTENCES]
    text = " ".join(sentences)

    words = text.split(" ")
    if len(words) > MAX_WORDS:
        text = " ".join(words[:MAX_WORDS]).rstrip(",;:")
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS].rsplit(" ", 1)[0].rstrip(",;:")
    if text[-1] not in ".!?…":
        text += "."
    return text
