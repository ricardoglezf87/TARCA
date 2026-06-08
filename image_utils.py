# -*- coding: utf-8 -*-
import base64
import os
from io import BytesIO

from PIL import Image


DEFAULT_IMAGE_MAX_SIZE = 1600
DEFAULT_IMAGE_JPEG_QUALITY = 82


def env_int(nombre, default):
    valor = os.getenv(nombre)
    if not valor:
        return default
    try:
        return int(valor)
    except ValueError:
        print(f"Valor invalido para {nombre}: {valor}. Se usa {default}.")
        return default


def imagen_optimizada(ruta_imagen):
    with Image.open(ruta_imagen) as imagen_original:
        imagen = imagen_original.convert("RGB")
        max_size = env_int("IMAGE_MAX_SIZE", DEFAULT_IMAGE_MAX_SIZE)
        if max_size > 0:
            imagen.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        return imagen.copy()


def imagen_a_data_url(ruta_imagen):
    imagen = imagen_optimizada(ruta_imagen)
    buffer = BytesIO()
    calidad = env_int("IMAGE_JPEG_QUALITY", DEFAULT_IMAGE_JPEG_QUALITY)
    imagen.save(buffer, format="JPEG", quality=calidad, optimize=True)
    imagen_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/jpeg;base64,{imagen_base64}"
