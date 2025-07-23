# -*- coding: utf-8 -*-

# Prompt para Gemini
PROMPT_PARA_GEMINI = """Analiza la pregunta y las opciones en la imagen.
Devuelve ÚNICAMENTE la letra de la opción u opciones correctas, comenzando desde A.
- Si solo hay una respuesta correcta (p. ej., la segunda opción), devuelve: B
- Si hay varias respuestas correctas (p. ej., la primera y la tercera), devuelve las letras juntas: AC
- No añadas texto, explicaciones, ni la palabra "respuesta". Solo las letras."""

# Prompt mejorado para Google Search
PROMPT_PARA_GOOGLE_SEARCH = """Tu tarea es analizar la imagen que contiene una pregunta de opción múltiple.
Basado en la pregunta y las opciones, y utilizando la información de búsqueda si es necesario, determina la(s) respuesta(s) correcta(s).

Tu respuesta DEBE ser ÚNICAMENTE la letra o letras de las opciones correctas.

- Formato para una sola respuesta correcta: B
- Formato para múltiples respuestas correctas: AC

NO incluyas NINGÚN texto adicional, explicaciones, saludos, o la palabra "respuesta".
SOLO las letras.

Ejemplo de respuesta esperada:
A
"""
