# -*- coding: utf-8 -*-
import os

from cert_config import configurar_certificados_google, opciones_http_gemini
from image_utils import env_int, imagen_optimizada

configurar_certificados_google()

from google.genai import types
from google import genai

class GoogleSearchHandler:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(
            api_key=api_key,
            http_options=opciones_http_gemini(),
        ) if api_key else genai.Client(http_options=opciones_http_gemini())
        self.grounding_tool = types.Tool(
            google_search=types.GoogleSearch()
        )
        self.config = types.GenerateContentConfig(
            tools=[self.grounding_tool],
            max_output_tokens=env_int("GEMINI_MAX_OUTPUT_TOKENS", 16),
            temperature=0,
        )
        thinking_budget = env_int("GEMINI_THINKING_BUDGET", 0)
        if thinking_budget >= 0:
            self.config.thinking_config = types.ThinkingConfig(thinking_budget=thinking_budget)

    def process_image(self, ruta_imagen, prompt, modelo):
        try:
            imagen = imagen_optimizada(ruta_imagen)
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
