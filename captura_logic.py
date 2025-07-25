# -*- coding: utf-8 -*-
import os
import threading
from datetime import datetime
import mss
import mss.tools
import pyautogui
from pynput import keyboard, mouse

# --- Configuración ---
CAPTURE_FOLDER = "capturas"
COOLDOWN_CAPTURA_SEGUNDOS = 2  # Tiempo de espera en segundos entre capturas
captura_en_cooldown = False

def obtener_monitor_con_cursor():
    """Determina en qué monitor se encuentra el cursor."""
    try:
        mouse_x, mouse_y = pyautogui.position()
    except Exception as e:
        print(f"Error al obtener la posición del cursor con PyAutoGUI: {e}")
        return None

    sct = mss.mss()
    monitores = sct.monitors

    if not monitores:
        print("Error: No se pudieron detectar monitores.")
        return None

    for i, monitor_details in enumerate(monitores):
        if i == 0: continue
        if (monitor_details["left"] <= mouse_x < monitor_details["left"] + monitor_details["width"] and
                monitor_details["top"] <= mouse_y < monitor_details["top"] + monitor_details["height"]):
            return monitor_details

    return monitores[1] if len(monitores) > 1 else monitores[0]

def realizar_captura_pantalla():
    """Captura el monitor donde está el cursor y guarda la imagen."""
    global captura_en_cooldown
    monitor_a_capturar = obtener_monitor_con_cursor()
    if not monitor_a_capturar:
        captura_en_cooldown = False
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

    except Exception as e:
        print(f"Error al capturar la pantalla: {e}")
    finally:
        threading.Timer(COOLDOWN_CAPTURA_SEGUNDOS, resetear_cooldown_captura).start()

def resetear_cooldown_captura():
    """Resetea la bandera captura_en_cooldown después del cooldown."""
    global captura_en_cooldown
    captura_en_cooldown = False

def al_presionar_tecla(tecla):
    """Callback que se ejecuta cuando se presiona una tecla."""
    global captura_en_cooldown
    try:
        if tecla == keyboard.Key.f2 and not captura_en_cooldown:
            captura_en_cooldown = True
            threading.Thread(target=realizar_captura_pantalla).start()
    except Exception as e:
        print(f"Error en el callback de tecla: {e}")

def al_hacer_clic_raton(x, y, button, pressed):
    """Callback que se ejecuta cuando se hace clic con el ratón."""
    global captura_en_cooldown
    try:
        if pressed and button == mouse.Button.x2 and not captura_en_cooldown:
            captura_en_cooldown = True
            threading.Thread(target=realizar_captura_pantalla).start()
    except Exception as e:
        print(f"Error en el callback de clic del ratón: {e}")

def iniciar_escucha_teclado():
    """Inicia el listener para la tecla F2."""
    with keyboard.Listener(on_press=al_presionar_tecla) as listener:
        listener.join()

def iniciar_escucha_raton():
    """Inicia el listener para el botón 'Avanzar Página' del ratón."""
    with mouse.Listener(on_click=al_hacer_clic_raton) as listener:
        listener.join()
