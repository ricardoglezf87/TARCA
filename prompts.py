# -*- coding: utf-8 -*-

PROMPT_PARA_IA = """Analiza la pregunta y las opciones en la imagen.
Devuelve UNICAMENTE la letra de la opcion u opciones correctas, comenzando desde A.
- Si solo hay una respuesta correcta (por ejemplo, la segunda opcion), devuelve: B
- Si hay varias respuestas correctas (por ejemplo, la primera y la tercera), devuelve las letras juntas: AC
- No anadas texto, explicaciones ni la palabra "respuesta". Solo las letras."""

PROMPT_PARA_GEMINI = PROMPT_PARA_IA
PROMPT_PARA_GPT = PROMPT_PARA_IA

PROMPT_PARA_GOOGLE_SEARCH = """Tu tarea es analizar la imagen que contiene una pregunta de opcion multiple.
Basado en la pregunta y las opciones, y utilizando informacion de busqueda si es necesario, determina la(s) respuesta(s) correcta(s).

Tu respuesta DEBE ser UNICAMENTE la letra o letras de las opciones correctas.

- Formato para una sola respuesta correcta: B
- Formato para multiples respuestas correctas: AC

NO incluyas texto adicional, explicaciones, saludos ni la palabra "respuesta".
SOLO las letras."""
