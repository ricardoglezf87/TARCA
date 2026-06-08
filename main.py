# -*- coding: utf-8 -*-
import os
import threading

from dotenv import load_dotenv
from watchdog.observers import Observer

from ai_handler import ManejadorCapturas
from app_lock import acquire_single_instance_lock
from captura_logic import iniciar_escucha_raton, iniciar_escucha_teclado
from ticker_display import initialize_ticker


CAPTURE_FOLDER = "capturas"


def main():
    instance_lock = acquire_single_instance_lock()
    if not instance_lock:
        print("TARCA ya esta en ejecucion. Cierra la instancia anterior desde el icono de bandeja.")
        return

    observador = None
    try:
        load_dotenv()

        ninja_mode_default_str = os.getenv("NINJA_MODE_DEFAULT", "false").lower()
        ninja_mode_initial_state = ninja_mode_default_str in ("true", "1", "t", "y", "yes")

        if not os.path.exists(CAPTURE_FOLDER):
            try:
                os.makedirs(CAPTURE_FOLDER)
                print(f"Carpeta de capturas '{CAPTURE_FOLDER}' creada.")
            except OSError as exc:
                print(f"Error al crear la carpeta de capturas '{CAPTURE_FOLDER}': {exc}")
                return

        shutdown_event = threading.Event()
        initialize_ticker(shutdown_event, ninja_mode_initial_state=ninja_mode_initial_state)

        hilo_escucha_teclado = threading.Thread(target=iniciar_escucha_teclado, daemon=True)
        hilo_escucha_teclado.start()

        hilo_escucha_raton = threading.Thread(target=iniciar_escucha_raton, daemon=True)
        hilo_escucha_raton.start()

        print(f"Las capturas se guardaran en la carpeta '{CAPTURE_FOLDER}'.")
        manejador_eventos = ManejadorCapturas()
        observador = Observer()
        try:
            observador.schedule(manejador_eventos, CAPTURE_FOLDER, recursive=False)
            observador.start()
            print(f"Monitoreando la carpeta '{CAPTURE_FOLDER}' para nuevas capturas...")
        except Exception as exc:
            print(f"Error al iniciar el observador de archivos en '{CAPTURE_FOLDER}': {exc}")
            return

        try:
            shutdown_event.wait()
        except KeyboardInterrupt:
            print("\nCierre solicitado por el usuario (Ctrl+C)...")
        finally:
            print("Iniciando secuencia de apagado...")
            if observador:
                observador.stop()
                observador.join()
            print("Aplicacion detenida correctamente.")
    finally:
        instance_lock.release()


if __name__ == "__main__":
    main()
