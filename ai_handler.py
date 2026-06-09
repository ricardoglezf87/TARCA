# -*- coding: utf-8 -*-
import os
import re
import time

from watchdog.events import FileSystemEventHandler

from cert_config import configurar_certificados_google, opciones_http_gemini
from image_utils import imagen_optimizada
from prompts import PROMPT_PARA_GEMINI, PROMPT_PARA_GOOGLE_SEARCH
from ticker_display import reset_to_default_state, show_processing_state, update_ticker


DEFAULT_GEMINI_MODEL = "gemini-3.5-flash"
DEFAULT_GEMINI_FALLBACK_MODELS = [
    "gemini-3.1-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.5-pro",
]
DEFAULT_GEMINI_MAX_OUTPUT_TOKENS = 16
DEFAULT_GEMINI_THINKING_BUDGET = 0
DEFAULT_CAPTURE_WRITE_DELAY_SECONDS = 0.15
VALID_PROVIDERS = {"auto", "gemini"}


def _env_bool(nombre, default=False):
    valor = os.getenv(nombre)
    if valor is None:
        return default
    return valor.strip().lower() in {"1", "true", "t", "yes", "y", "si", "s"}


def _env_int(nombre, default):
    valor = os.getenv(nombre)
    if not valor:
        return default
    try:
        return int(valor)
    except ValueError:
        print(f"Valor invalido para {nombre}: {valor}. Se usa {default}.")
        return default


def _env_float(nombre, default):
    valor = os.getenv(nombre)
    if not valor:
        return default
    try:
        return float(valor)
    except ValueError:
        print(f"Valor invalido para {nombre}: {valor}. Se usa {default}.")
        return default


def _cadena_causas_error(exc):
    causas = []
    actual = exc
    visitadas = set()
    while actual and id(actual) not in visitadas:
        visitadas.add(id(actual))
        causas.append(f"{type(actual).__name__}: {actual}")
        actual = getattr(actual, "__cause__", None) or getattr(actual, "__context__", None)
    return " | ".join(causas)


def _normalizar_respuesta_letras(texto):
    if not texto:
        return ""

    for linea in texto.splitlines():
        compacta = re.sub(r"[\s,.;:/\\|+_-]+", "", linea.strip().upper())
        if compacta and re.fullmatch(r"[A-H]+", compacta):
            return compacta

    coincidencia = re.search(r"\b([A-H](?:[\s,;/+]*[A-H])*)\b", texto.upper())
    if coincidencia:
        return re.sub(r"[^A-H]", "", coincidencia.group(1))

    return texto.strip()


class ManejadorCapturas(FileSystemEventHandler):
    """Maneja nuevas capturas y las envia al proveedor de IA configurado."""

    def __init__(self):
        self.archivos_procesados = set()
        self.proveedor_ia = self._resolver_proveedor_ia()
        self.cliente_gemini = None
        print(f"Proveedor de IA activo: {self.proveedor_ia}")

    def _resolver_proveedor_ia(self):
        proveedor = os.getenv("AI_PROVIDER", "").strip().lower()
        if not proveedor:
            proveedor = "auto"

        if proveedor not in VALID_PROVIDERS:
            print(f"AI_PROVIDER invalido: {proveedor}. Se usara gemini.")
        return "gemini"

    def _modelos_gemini_para_intentar(self):
        modelos = [os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL).strip() or DEFAULT_GEMINI_MODEL]
        fallback_raw = os.getenv("GEMINI_FALLBACK_MODELS", "")
        fallbacks = (
            [modelo.strip() for modelo in fallback_raw.split(",") if modelo.strip()]
            if fallback_raw
            else DEFAULT_GEMINI_FALLBACK_MODELS
        )

        for modelo in fallbacks:
            if modelo not in modelos:
                modelos.append(modelo)
        return modelos

    def on_created(self, evento):
        if evento.is_directory or not evento.src_path.lower().endswith((".png", ".jpg", ".jpeg")):
            return

        time.sleep(_env_float("CAPTURE_WRITE_DELAY_SECONDS", DEFAULT_CAPTURE_WRITE_DELAY_SECONDS))
        if evento.src_path in self.archivos_procesados:
            return

        self.archivos_procesados.add(evento.src_path)
        print(f"\nNueva captura detectada: {evento.src_path}")
        self.procesar_captura(evento.src_path)

    def procesar_captura(self, ruta_imagen):
        show_processing_state()

        if not os.path.exists(ruta_imagen):
            print(f"Error: archivo de imagen no encontrado: {ruta_imagen}")
            self._restaurar_para_reintento(ruta_imagen)
            return

        ultimo_error = None
        modelos = self._modelos_gemini_para_intentar()
        for indice, modelo in enumerate(modelos):
            inicio = time.perf_counter()
            try:
                texto_respuesta = self._procesar_con_gemini(ruta_imagen, modelo)

                if texto_respuesta:
                    duracion = time.perf_counter() - inicio
                    print(f"Tiempo gemini ({modelo}): {duracion:.2f}s")
                    print(f"Respuesta gemini ({modelo}): {texto_respuesta}")
                    update_ticker(texto_respuesta)
                    return

                print(f"Gemini ({modelo}) no devolvio contenido util en {time.perf_counter() - inicio:.2f}s.")
            except Exception as exc:
                ultimo_error = exc
                print(f"Error al procesar captura con Gemini ({modelo}) tras {time.perf_counter() - inicio:.2f}s: {exc}")
                print(f"Detalle tecnico: {_cadena_causas_error(exc)}")

            if indice < len(modelos) - 1:
                print(f"Intentando modelo Gemini de respaldo: {modelos[indice + 1]}...")

        if ultimo_error:
            print("No se pudo obtener respuesta de ningun proveedor disponible.")
        else:
            print("La IA no devolvio contenido util. Verifica la imagen o el prompt.")
        self._restaurar_para_reintento(ruta_imagen)

    def _restaurar_para_reintento(self, ruta_imagen):
        self.archivos_procesados.discard(ruta_imagen)
        reset_to_default_state()

    def _procesar_con_gemini(self, ruta_imagen, modelo):
        if _env_bool("GOOGLE_SEARCH", False):
            configurar_certificados_google()
            from google_search_handler import GoogleSearchHandler

            google_handler = GoogleSearchHandler()
            texto_respuesta = google_handler.process_image(
                ruta_imagen, PROMPT_PARA_GOOGLE_SEARCH, modelo
            )
            return _normalizar_respuesta_letras(texto_respuesta)

        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY no esta configurada.")

        configurar_certificados_google()

        if self.cliente_gemini is None:
            from google import genai

            self.cliente_gemini = genai.Client(
                api_key=gemini_api_key,
                http_options=opciones_http_gemini(),
            )
            print("Cliente Gemini inicializado.")

        print(f"Enviando '{os.path.basename(ruta_imagen)}' a Gemini...")
        imagen = imagen_optimizada(ruta_imagen)

        from google.genai import types

        config = types.GenerateContentConfig(
            max_output_tokens=_env_int(
                "GEMINI_MAX_OUTPUT_TOKENS",
                DEFAULT_GEMINI_MAX_OUTPUT_TOKENS,
            ),
            temperature=0,
        )
        thinking_budget = _env_int("GEMINI_THINKING_BUDGET", DEFAULT_GEMINI_THINKING_BUDGET)
        if thinking_budget >= 0:
            config.thinking_config = types.ThinkingConfig(thinking_budget=thinking_budget)

        respuesta = self.cliente_gemini.models.generate_content(
            model=modelo,
            contents=[PROMPT_PARA_GEMINI, imagen],
            config=config,
        )

        texto = getattr(respuesta, "text", None)
        if not texto:
            print("Gemini no devolvio contenido.")
            return None

        return _normalizar_respuesta_letras(texto)
