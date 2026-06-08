# -*- coding: utf-8 -*-
import base64
import mimetypes
import os
import re
import ssl
import time

from PIL import Image
from watchdog.events import FileSystemEventHandler

from prompts import PROMPT_PARA_GEMINI, PROMPT_PARA_GOOGLE_SEARCH, PROMPT_PARA_GPT
from ticker_display import reset_to_default_state, show_processing_state, update_ticker


DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
DEFAULT_OPENAI_MODEL = "gpt-5.4-mini"
DEFAULT_OPENAI_MAX_OUTPUT_TOKENS = 128
DEFAULT_OPENAI_TIMEOUT_SECONDS = 60
VALID_PROVIDERS = {"openai", "gemini"}


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


def _configuracion_ssl_openai():
    if not _env_bool("OPENAI_SSL_VERIFY", True):
        print("Advertencia: OPENAI_SSL_VERIFY=false desactiva la verificacion SSL.")
        return False

    ca_bundle = os.getenv("OPENAI_CA_BUNDLE")
    if ca_bundle:
        return ca_bundle

    if _env_bool("OPENAI_USE_SYSTEM_CERTS", True):
        try:
            import truststore

            return truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        except ImportError:
            print("truststore no esta instalado; se usaran los certificados por defecto de Python.")

    return True


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


def _imagen_a_data_url(ruta_imagen):
    mime_type = mimetypes.guess_type(ruta_imagen)[0] or "image/png"
    with open(ruta_imagen, "rb") as archivo:
        imagen_base64 = base64.b64encode(archivo.read()).decode("utf-8")
    return f"data:{mime_type};base64,{imagen_base64}"


def _extraer_texto_openai(respuesta):
    texto = getattr(respuesta, "output_text", None)
    if texto:
        return texto

    partes_texto = []
    for item in getattr(respuesta, "output", []) or []:
        for contenido in getattr(item, "content", []) or []:
            texto_contenido = getattr(contenido, "text", None)
            if texto_contenido:
                partes_texto.append(texto_contenido)
    return "\n".join(partes_texto)


class OpenAIImageHandler:
    def __init__(self, modelo=None, usar_busqueda=False):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.modelo = modelo or os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)
        self.usar_busqueda = usar_busqueda
        self.timeout_seconds = _env_float("OPENAI_TIMEOUT_SECONDS", DEFAULT_OPENAI_TIMEOUT_SECONDS)
        self.trust_env = _env_bool("OPENAI_TRUST_ENV", False)
        self.client = None

    def _obtener_cliente(self):
        if self.client is None:
            if not self.api_key:
                raise RuntimeError("OPENAI_API_KEY no esta configurada.")
            import httpx
            from openai import OpenAI

            http_client = httpx.Client(
                timeout=self.timeout_seconds,
                trust_env=self.trust_env,
                verify=_configuracion_ssl_openai(),
            )
            self.client = OpenAI(
                api_key=self.api_key,
                http_client=http_client,
                max_retries=_env_int("OPENAI_MAX_RETRIES", 2),
            )
        return self.client

    def process_image(self, ruta_imagen, prompt):
        data_url = _imagen_a_data_url(ruta_imagen)
        peticion = {
            "model": self.modelo,
            "input": [
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt},
                        {"type": "input_image", "image_url": data_url},
                    ],
                }
            ],
            "max_output_tokens": _env_int(
                "OPENAI_MAX_OUTPUT_TOKENS", DEFAULT_OPENAI_MAX_OUTPUT_TOKENS
            ),
        }

        if self.usar_busqueda:
            peticion["tools"] = [{"type": "web_search"}]
            peticion["tool_choice"] = "auto"

        respuesta = self._obtener_cliente().responses.create(**peticion)
        return _normalizar_respuesta_letras(_extraer_texto_openai(respuesta))


class ManejadorCapturas(FileSystemEventHandler):
    """Maneja nuevas capturas y las envia al proveedor de IA configurado."""

    def __init__(self):
        self.archivos_procesados = set()
        self.proveedor_ia = self._resolver_proveedor_ia()
        self.openai_handler = None
        self.modelo_gemini = None
        print(f"Proveedor de IA activo: {self.proveedor_ia}")

    def _resolver_proveedor_ia(self):
        proveedor = os.getenv("AI_PROVIDER", "").strip().lower()
        if not proveedor:
            return "openai" if os.getenv("OPENAI_API_KEY") else "gemini"

        if proveedor not in VALID_PROVIDERS:
            print(f"AI_PROVIDER invalido: {proveedor}. Se usara openai.")
            return "openai"
        return proveedor

    def on_created(self, evento):
        if evento.is_directory or not evento.src_path.lower().endswith((".png", ".jpg", ".jpeg")):
            return

        time.sleep(0.5)
        if evento.src_path in self.archivos_procesados:
            return

        self.archivos_procesados.add(evento.src_path)
        print(f"\nNueva captura detectada: {evento.src_path}")
        self.procesar_captura(evento.src_path)

    def procesar_captura(self, ruta_imagen):
        show_processing_state()
        try:
            if self.proveedor_ia == "openai":
                texto_respuesta = self._procesar_con_openai(ruta_imagen)
            else:
                texto_respuesta = self._procesar_con_gemini(ruta_imagen)

            if not texto_respuesta:
                print("La IA no devolvio contenido util. Verifica la imagen o el prompt.")
                self._restaurar_para_reintento(ruta_imagen)
                return

            print(f"Respuesta {self.proveedor_ia}: {texto_respuesta}")
            update_ticker(texto_respuesta)
        except FileNotFoundError:
            print(f"Error: archivo de imagen no encontrado: {ruta_imagen}")
            self._restaurar_para_reintento(ruta_imagen)
        except Exception as exc:
            print(f"Error al procesar captura con {self.proveedor_ia}: {exc}")
            print(f"Detalle tecnico: {_cadena_causas_error(exc)}")
            self._restaurar_para_reintento(ruta_imagen)

    def _restaurar_para_reintento(self, ruta_imagen):
        self.archivos_procesados.discard(ruta_imagen)
        reset_to_default_state()

    def _procesar_con_openai(self, ruta_imagen):
        if self.openai_handler is None:
            self.openai_handler = OpenAIImageHandler(
                modelo=os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL),
                usar_busqueda=_env_bool("OPENAI_WEB_SEARCH", False),
            )

        print(f"Enviando '{os.path.basename(ruta_imagen)}' a OpenAI...")
        return self.openai_handler.process_image(ruta_imagen, PROMPT_PARA_GPT)

    def _procesar_con_gemini(self, ruta_imagen):
        modelo = os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)

        if _env_bool("GOOGLE_SEARCH", False):
            from google_search_handler import GoogleSearchHandler

            google_handler = GoogleSearchHandler()
            texto_respuesta = google_handler.process_image(
                ruta_imagen, PROMPT_PARA_GOOGLE_SEARCH, modelo
            )
            return _normalizar_respuesta_letras(texto_respuesta)

        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY no esta configurada.")

        if self.modelo_gemini is None:
            import google.generativeai as genai

            genai.configure(api_key=gemini_api_key)
            self.modelo_gemini = genai.GenerativeModel(modelo)
            print("Modelo Gemini inicializado.")

        print(f"Enviando '{os.path.basename(ruta_imagen)}' a Gemini...")
        with Image.open(ruta_imagen) as imagen:
            respuesta = self.modelo_gemini.generate_content([PROMPT_PARA_GEMINI, imagen])

        if not getattr(respuesta, "parts", None):
            razon_bloqueo = "No especificada"
            feedback = getattr(respuesta, "prompt_feedback", None)
            if feedback and getattr(feedback, "block_reason", None):
                razon_bloqueo = feedback.block_reason
                print(f"La solicitud a Gemini fue bloqueada. Razon: {razon_bloqueo}")
                for rating in getattr(feedback, "safety_ratings", []) or []:
                    print(f"  Categoria: {rating.category}, Probabilidad: {rating.probability}")
            else:
                print("Gemini no devolvio contenido.")
            return None

        return _normalizar_respuesta_letras(respuesta.text)
