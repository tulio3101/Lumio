"""Validación de la foto antes de enviarla al VLM (ADR-308 §2 y §6).

Solo se leen los encabezados del JPEG (sin decodificarlo ni guardarlo): basta para saber que
es un JPEG y cuánto mide su lado largo.
"""

MAX_IMAGE_BYTES = 1024 * 1024
MAX_LONG_SIDE_PX = 1024

# Marcadores SOF (Start Of Frame) que llevan alto y ancho; excluye DHT (C4), JPG (C8) y DAC (CC).
_SOF_MARKERS = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}


def jpeg_size(data: bytes) -> tuple[int, int] | None:
    """(ancho, alto) del JPEG, o None si no es un JPEG legible."""
    if len(data) < 4 or data[:2] != b"\xff\xd8":
        return None
    index = 2
    while index + 4 <= len(data):
        if data[index] != 0xFF:
            return None
        marker = data[index + 1]
        if marker == 0xFF:  # relleno entre marcadores
            index += 1
            continue
        if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:  # sin longitud
            index += 2
            continue
        length = int.from_bytes(data[index + 2 : index + 4], "big")
        if length < 2:
            return None
        if marker in _SOF_MARKERS:
            if index + 9 > len(data):
                return None
            height = int.from_bytes(data[index + 5 : index + 7], "big")
            width = int.from_bytes(data[index + 7 : index + 9], "big")
            return (width, height) if width and height else None
        if marker == 0xDA:  # empieza la imagen sin haber visto el tamaño
            return None
        index += 2 + length
    return None
