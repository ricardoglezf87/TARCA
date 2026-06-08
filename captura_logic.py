# -*- coding: utf-8 -*-
import os
import threading
import time
from datetime import datetime

import mss
import mss.tools
import pyautogui
from pynput import keyboard, mouse


CAPTURE_FOLDER = "capturas"
COOLDOWN_CAPTURA_SEGUNDOS = 2

captura_en_cooldown = False
ultimo_disparo_captura = 0.0
captura_lock = threading.Lock()


def obtener_monitor_con_cursor():
    """Determina en que monitor se encuentra el cursor."""
    try:
        mouse_x, mouse_y = pyautogui.position()
    except Exception as exc:
        print(f"Error al obtener la posicion del cursor con PyAutoGUI: {exc}")
        return None

    with mss.mss() as sct:
        monitores = sct.monitors

    if not monitores:
        print("Error: no se pudieron detectar monitores.")
        return None

    for indice, monitor_details in enumerate(monitores):
        if indice == 0:
            continue
        if (
            monitor_details["left"] <= mouse_x < monitor_details["left"] + monitor_details["width"]
            and monitor_details["top"] <= mouse_y < monitor_details["top"] + monitor_details["height"]
        ):
            return monitor_details

    return monitores[1] if len(monitores) > 1 else monitores[0]


def realizar_captura_pantalla():
    """Captura el monitor donde esta el cursor y guarda la imagen."""
    monitor_a_capturar = obtener_monitor_con_cursor()
    if not monitor_a_capturar:
        resetear_cooldown_captura()
        return

    try:
        if not os.path.exists(CAPTURE_FOLDER):
            os.makedirs(CAPTURE_FOLDER)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        nombre_archivo = os.path.join(CAPTURE_FOLDER, f"captura_{timestamp}.png")

        with mss.mss() as sct:
            imagen_capturada = sct.grab(monitor_a_capturar)
            mss.tools.to_png(imagen_capturada.rgb, imagen_capturada.size, output=nombre_archivo)

        print(f"Captura guardada en: {nombre_archivo}")
    except Exception as exc:
        print(f"Error al capturar la pantalla: {exc}")
    finally:
        threading.Timer(COOLDOWN_CAPTURA_SEGUNDOS, resetear_cooldown_captura).start()


def resetear_cooldown_captura():
    """Resetea la bandera de cooldown."""
    global captura_en_cooldown
    with captura_lock:
        captura_en_cooldown = False


def solicitar_captura(origen):
    """Solicita una captura con bloqueo atomico para evitar duplicados."""
    global captura_en_cooldown, ultimo_disparo_captura
    ahora = time.monotonic()

    with captura_lock:
        if captura_en_cooldown:
            return
        if ahora - ultimo_disparo_captura < COOLDOWN_CAPTURA_SEGUNDOS:
            return

        captura_en_cooldown = True
        ultimo_disparo_captura = ahora

    threading.Thread(
        target=realizar_captura_pantalla,
        name=f"captura-{origen}",
        daemon=True,
    ).start()


def al_presionar_tecla(tecla):
    """Callback que se ejecuta cuando se presiona una tecla."""
    try:
        if tecla == keyboard.Key.f2:
            solicitar_captura("teclado")
    except Exception as exc:
        print(f"Error en el callback de tecla: {exc}")


def al_hacer_clic_raton(x, y, button, pressed):
    """Callback que se ejecuta cuando se hace clic con el raton."""
    try:
        if pressed and button == mouse.Button.x2:
            solicitar_captura("raton")
    except Exception as exc:
        print(f"Error en el callback de clic del raton: {exc}")


def iniciar_escucha_teclado():
    """Inicia el listener para la tecla F2."""
    with keyboard.Listener(on_press=al_presionar_tecla) as listener:
        listener.join()


def iniciar_escucha_raton():
    """Inicia el listener para el boton lateral x2 del raton."""
    with mouse.Listener(on_click=al_hacer_clic_raton) as listener:
        listener.join()
