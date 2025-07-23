# -*- coding: utf-8 -*-

# Prompt para Gemini
PROMPT_PARA_GEMINI = """Analiza la pregunta y las opciones en la imagen.
Devuelve ÚNICAMENTE la letra de la opción u opciones correctas, comenzando desde A.
- Si solo hay una respuesta correcta (p. ej., la segunda opción), devuelve: B
- Si hay varias respuestas correctas (p. ej., la primera y la tercera), devuelve las letras juntas: AC
- No añadas texto, explicaciones, ni la palabra "respuesta". Solo las letras."""

# Prompt mejorado para Google Search
PROMPT_PARA_GOOGLE_SEARCH = """Analiza la pregunta y las opciones en la imagen.
Devuelve exclusivamente las letras de las opciones correctas, comenzando desde A.
- Si solo hay una respuesta correcta (por ejemplo, la segunda opción), devuelve: B
- Si hay varias respuestas correctas (por ejemplo, la primera y la tercera), devuelve las letras juntas: AC
- No incluyas explicaciones, comentarios adicionales ni palabras como "respuesta". Solo las letras."""
