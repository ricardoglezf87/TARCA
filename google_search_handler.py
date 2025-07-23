# -*- coding: utf-8 -*-
from google.genai import types
from google import genai
from PIL import Image

class GoogleSearchHandler:
    def __init__(self):
        self.client = genai.Client()
        self.grounding_tool = types.Tool(
            google_search=types.GoogleSearch()
        )
        self.config = types.GenerateContentConfig(
            tools=[self.grounding_tool]
        )

    def process_image(self, ruta_imagen, prompt, modelo):
        try:
            imagen = Image.open(ruta_imagen)
            respuesta = self.client.models.generate_content(
                model=modelo,
                contents=[prompt, imagen],
                config=self.config,
            )
            if not respuesta or not respuesta.candidates[0].content.parts[0]:
                return None
            return respuesta.candidates[0].content.parts[0].text.strip()
        except Exception as e:
            print(f"Error al procesar con Google Search: {e}")
            return None
