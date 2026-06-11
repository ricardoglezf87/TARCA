# -*- coding: utf-8 -*-
import os


PROMPT_PARA_IA = """Analiza la pregunta y las opciones en la imagen.
Sigue siempre las instrucciones del Gem si estan disponibles.
Si no hay instrucciones del Gem, responde con el formato:
- Respuesta: a
- Respuesta: a, c
No anadas explicaciones salvo que el usuario las pida."""

PROMPT_PARA_GEMINI = PROMPT_PARA_IA

PROMPT_METODO_ANTIGUO = """Analiza la pregunta y las opciones en la imagen.
Usa el metodo anterior: responde segun el contenido visible en la captura, sin exigir evidencia en los archivos locales.

Formato obligatorio:
- Respuesta: a
- Respuesta: a, c

No anadas explicaciones salvo que el usuario las pida.
Si la captura no se lee bien, responde: Respuesta: captura no legible"""

PROMPT_PARA_GOOGLE_SEARCH = """Tu tarea es analizar la imagen que contiene una pregunta de opcion multiple.
Basado en la pregunta y las opciones, y utilizando informacion de busqueda si es necesario, determina la(s) respuesta(s) correcta(s).

Tu respuesta DEBE ser UNICAMENTE la letra o letras de las opciones correctas.

- Formato para una sola respuesta correcta: B
- Formato para multiples respuestas correctas: AC

NO incluyas texto adicional, explicaciones, saludos ni la palabra "respuesta".
SOLO las letras."""


def cargar_instrucciones_gem():
    ruta = os.getenv("GEMINI_GEM_INSTRUCTIONS_FILE", "gem_instructions.md").strip()
    if not ruta or not os.path.exists(ruta):
        return ""

    try:
        with open(ruta, "r", encoding="utf-8") as archivo:
            return archivo.read().strip()
    except OSError as exc:
        print(f"No se pudieron leer las instrucciones del Gem ({ruta}): {exc}")
        return ""


def construir_prompt_gemini(contexto_proyecto=""):
    instrucciones_gem = cargar_instrucciones_gem()
    partes = []

    if instrucciones_gem:
        partes.append(
            f"""Usa estas instrucciones y contexto del Gem como informacion prioritaria.
Si alguna regla de abajo contradice el prompt base, obedecen las instrucciones del Gem:

{instrucciones_gem}"""
        )

    if contexto_proyecto:
        partes.append(
            f"""Fragmentos encontrados en los archivos locales del proyecto.
Usa unicamente estos fragmentos como evidencia documental:

{contexto_proyecto}"""
        )
    else:
        partes.append(
            "No se encontraron fragmentos locales del proyecto para esta pregunta. Si las instrucciones exigen evidencia documental, responde: Respuesta: no encontrada en archivos"
        )

    partes.append(PROMPT_PARA_GEMINI)
    return "\n\n---\n\n".join(partes)
