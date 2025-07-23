# -*- coding: utf-8 -*-
import os
import threading
from dotenv import load_dotenv
from watchdog.observers import Observer
from captura_logic import iniciar_escucha_teclado, iniciar_escucha_raton
from gemini_handler import ManejadorCapturas
from ticker_display import initialize_ticker

# --- Configuración ---
CAPTURE_FOLDER = "capturas"
MODELO_GEMINI = 'gemini-2.5-flash'

def main():
    # Cargar variables de entorno del archivo .env (si existe)
    load_dotenv()
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    ninja_mode_default_str = os.getenv("NINJA_MODE_DEFAULT", "false").lower()
    ninja_mode_initial_state = ninja_mode_default_str in ('true', '1', 't', 'y', 'yes')

    if not GEMINI_API_KEY:
        print("Error Crítico: La API Key de Gemini no está configurada.")
        print("Por favor, crea un archivo .env con la línea: GEMINI_API_KEY='TU_API_KEY'")
        print("O establece la variable de entorno GEMINI_API_KEY.")
        return

    try:
        from google.generativeai import configure, GenerativeModel
        configure(api_key=GEMINI_API_KEY)
        modelo_gemini = GenerativeModel(MODELO_GEMINI)
        print(f"Modelo Gemini '{MODELO_GEMINI}' inicializado correctamente.")
    except Exception as e:
        print(f"Error al inicializar el modelo Gemini '{MODELO_GEMINI}': {e}")
        return

    if not os.path.exists(CAPTURE_FOLDER):
        try:
            os.makedirs(CAPTURE_FOLDER)
            print(f"Carpeta de capturas '{CAPTURE_FOLDER}' creada.")
        except OSError as e:
            print(f"Error al crear la carpeta de capturas '{CAPTURE_FOLDER}': {e}")
            return

    shutdown_event = threading.Event()
    initialize_ticker(shutdown_event, ninja_mode_initial_state=ninja_mode_initial_state)

    hilo_escucha_teclado = threading.Thread(target=iniciar_escucha_teclado, daemon=True)
    hilo_escucha_teclado.start()

    hilo_escucha_raton = threading.Thread(target=iniciar_escucha_raton, daemon=True)
    hilo_escucha_raton.start()

    print(f"Las capturas se guardarán en la carpeta '{CAPTURE_FOLDER}'.")
    manejador_eventos = ManejadorCapturas(modelo_gemini=modelo_gemini)
    observador = Observer()
    try:
        observador.schedule(manejador_eventos, CAPTURE_FOLDER, recursive=False)
        observador.start()
        print(f"Monitoreando la carpeta '{CAPTURE_FOLDER}' para nuevas capturas...")
    except Exception as e:
        print(f"Error al iniciar el observador de archivos en '{CAPTURE_FOLDER}': {e}")
        return

    try:
        shutdown_event.wait()
    except KeyboardInterrupt:
        print("\nCierre solicitado por el usuario (Ctrl+C)...")
    finally:
        print("Iniciando secuencia de apagado...")
        observador.stop()
        observador.join()
        print("Aplicación detenida correctamente.")

if __name__ == "__main__":
    main()
