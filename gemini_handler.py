# -*- coding: utf-8 -*-
import os
import time
from watchdog.events import FileSystemEventHandler
from PIL import Image
from google.genai import types
from ticker_display import update_ticker, reset_to_default_state, show_processing_state
from dotenv import load_dotenv
from prompts import PROMPT_PARA_GEMINI, PROMPT_PARA_GOOGLE_SEARCH

# --- Configuración ---
MODELO_GEMINI = 'gemini-2.5-flash'

class ManejadorCapturas(FileSystemEventHandler):
    """Clase para manejar eventos del sistema de archivos (nuevas capturas)."""
    def __init__(self):
        self.archivos_procesados = set()  # Para evitar procesar un archivo múltiples veces

    def on_created(self, evento):
        """Se llama cuando se crea un nuevo archivo en la carpeta monitoreada."""
        if not evento.is_directory and evento.src_path.lower().endswith(('.png', '.jpg', '.jpeg')):
            time.sleep(0.5)  # Pausa para asegurar que el archivo se haya escrito completamente
            
            if evento.src_path in self.archivos_procesados:
                return  # Ya procesado o en proceso

            self.archivos_procesados.add(evento.src_path)
            print(f"\nNueva captura detectada: {evento.src_path}")
            self.procesar_con_gemini(evento.src_path)    

    def procesar_con_gemini(self, ruta_imagen):
        """Envía la imagen a Gemini y muestra la respuesta."""
        show_processing_state()

        GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        GOOGLE_SEARCH = os.getenv ("GOOGLE_SEARCH", "false").lower()    
        
        if GOOGLE_SEARCH == "true":
            from google_search_handler import GoogleSearchHandler
            
            google_handler = GoogleSearchHandler()
            textoRespuesta = google_handler.process_image(
                ruta_imagen, PROMPT_PARA_GOOGLE_SEARCH, MODELO_GEMINI
            )
            
            if not textoRespuesta:
                print("Google Search no devolvió contenido. Verifica la imagen o el prompt.")
                reset_to_default_state()
                return
            
            print(textoRespuesta)
            update_ticker(textoRespuesta.strip())
        else:        
            import google.generativeai as genai
            
            if GEMINI_API_KEY:
                try:
                    genai.configure(api_key=GEMINI_API_KEY)
                    self.modelo_gemini = genai.GenerativeModel(MODELO_GEMINI)
                    print("Modelo Gemini inicializado.")
                except Exception as e:
                    print(f"Error al re-inicializar modelo Gemini: {e}")
                    self.archivos_procesados.discard(ruta_imagen)
                    reset_to_default_state()
                    return
            else:
                print("API Key de Gemini sigue sin encontrarse.")
                self.archivos_procesados.discard(ruta_imagen)
                reset_to_default_state()
                return

            try:
                print(f"Enviando '{os.path.basename(ruta_imagen)}' a Gemini...")
                imagen = Image.open(ruta_imagen)
                respuesta = self.modelo_gemini.generate_content([PROMPT_PARA_GEMINI, imagen])
                
                if not respuesta.parts:
                    razon_bloqueo = "No especificada"
                    if hasattr(respuesta, 'prompt_feedback') and respuesta.prompt_feedback.block_reason:
                        razon_bloqueo = respuesta.prompt_feedback.block_reason
                        print(f"La solicitud a Gemini fue bloqueada. Razón: {razon_bloqueo}")
                        if respuesta.prompt_feedback.safety_ratings:
                            for rating in respuesta.prompt_feedback.safety_ratings:
                                print(f"  Categoría de seguridad: {rating.category}, Probabilidad: {rating.probability}")
                    else:
                        print("Gemini no devolvió contenido. Verifica la imagen o el prompt.")
                    reset_to_default_state()
                    return
                
                update_ticker(respuesta.text.strip())
            except FileNotFoundError:
                print(f"Error: Archivo de imagen no encontrado durante el procesamiento: {ruta_imagen}")
                self.archivos_procesados.discard(ruta_imagen)
                reset_to_default_state()
            except Exception as e:
                print(f"Error al procesar con Gemini: {e}")
                if ruta_imagen in self.archivos_procesados:
                    self.archivos_procesados.discard(ruta_imagen)
                reset_to_default_state()
