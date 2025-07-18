# -*- coding: utf-8 -*-
import os
import time
import threading
from datetime import datetime
from ticker_display import initialize_ticker, update_ticker

# Para escuchar el teclado (F2) y el ratón
from pynput import keyboard, mouse

# Para captura de pantalla eficiente
import mss
import mss.tools

# Para obtener la posición del ratón
import pyautogui

# Para monitorear cambios en el sistema de archivos (nuevas capturas)
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Para interactuar con la API de Gemini
import google.generativeai as genai

# Para cargar variables de entorno (API Key)
from dotenv import load_dotenv

# Pillow para abrir la imagen antes de enviarla a Gemini
from PIL import Image

# --- Configuración ---
CAPTURE_FOLDER = "capturas"  # Carpeta para guardar las imágenes
# La API Key se cargará desde el archivo .env o variables de entorno
GEMINI_API_KEY = None
PROMPT_PARA_GEMINI = """Analiza la pregunta y las opciones en la imagen.
Devuelve ÚNICAMENTE la letra  de la opción u opciones correctas, comenzando desde A.
- Si solo hay una respuesta correcta (p. ej., la segunda opción), devuelve: B
- Si hay varias respuestas correctas (p. ej., la primera y la tercera), devuelve las letras juntas: AC
- No añadas texto, explicaciones, ni la palabra "respuesta". Solo las letras."""

MODELO_GEMINI = 'gemini-2.5-flash' # Modelo multimodal recomendado

# --- Lógica de Captura de Pantalla ---

# Bandera global y cooldown para evitar capturas múltiples
captura_en_cooldown = False
COOLDOWN_CAPTURA_SEGUNDOS = 2  # Tiempo de espera en segundos entre capturas

def obtener_monitor_con_cursor():
    """Determina en qué monitor se encuentra el cursor."""
    try:
        mouse_x, mouse_y = pyautogui.position()
    except Exception as e:
        print(f"Error al obtener la posición del cursor con PyAutoGUI: {e}")
        print("Asegúrate de que PyAutoGUI tiene los permisos necesarios (especialmente en Linux con Wayland o macOS).")
        return None

    sct = mss.mss()
    monitores = sct.monitors

    if not monitores:
        print("Error: No se pudieron detectar monitores.")
        return None

    # sct.monitors[0] es la pantalla virtual 'all-in-one'.
    # sct.monitors[1:] son los monitores físicos individuales.

    if len(monitores) > 1: # Múltiples monitores físicos detectados
        for i, monitor_details in enumerate(monitores):
            if i == 0: continue # Omitir el monitor 'all-in-one'
            
            # Comprobar si el cursor está dentro de los límites de este monitor
            if (monitor_details["left"] <= mouse_x < monitor_details["left"] + monitor_details["width"] and
                    monitor_details["top"] <= mouse_y < monitor_details["top"] + monitor_details["height"]):
                print(f"Cursor encontrado en el monitor: {monitor_details}")
                return monitor_details
        
        # Fallback: si el cursor no se encontró en un monitor específico (raro)
        print("Advertencia: Cursor no encontrado en un monitor físico específico. Usando el primer monitor físico como predeterminado.")
        return monitores[1] # Usualmente el monitor primario

    elif len(monitores) == 1: # Solo un monitor detectado (probablemente el 'all-in-one')
        print(f"Solo se detectó un monitor (posiblemente 'all-in-one'). Usando: {monitores[0]}")
        return monitores[0]
    
    print("Error: No se pudo determinar el monitor del cursor.")
    return None

def realizar_captura_pantalla():
    """Captura el monitor donde está el cursor y guarda la imagen."""
    global captura_en_cooldown
    
    monitor_a_capturar = obtener_monitor_con_cursor()
    if not monitor_a_capturar:
        print("No se pudo capturar la pantalla: monitor no encontrado.")
        captura_en_cooldown = False # Resetear flag si falla la detección del monitor
        return

    try:
        if not os.path.exists(CAPTURE_FOLDER):
            os.makedirs(CAPTURE_FOLDER)
            print(f"Carpeta '{CAPTURE_FOLDER}' creada.")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        nombre_archivo = os.path.join(CAPTURE_FOLDER, f"captura_{timestamp}.png")

        with mss.mss() as sct:
            # Capturar el monitor específico
            imagen_capturada = sct.grab(monitor_a_capturar)
            # Guardar la imagen
            mss.tools.to_png(imagen_capturada.rgb, imagen_capturada.size, output=nombre_archivo)
        
        print(f"Captura guardada en: {nombre_archivo}")

    except Exception as e:
        print(f"Error al capturar la pantalla: {e}")
    finally:
        # Iniciar un temporizador para resetear la bandera después del cooldown
        threading.Timer(COOLDOWN_CAPTURA_SEGUNDOS, resetear_cooldown_captura).start()

def resetear_cooldown_captura():
    """Resetea la bandera captura_en_cooldown después del cooldown."""
    global captura_en_cooldown
    captura_en_cooldown = False
    # print(f"Cooldown de captura terminado. Listo para nueva captura.") # Opcional: para depuración

def al_presionar_tecla(tecla):
    """Callback que se ejecuta cuando se presiona una tecla."""
    global captura_en_cooldown
    try:
        if tecla == keyboard.Key.f2 and not captura_en_cooldown:
            captura_en_cooldown = True # Marcar como en cooldown
            print("F2 presionado! Realizando captura...")
            # Realizar la captura en un nuevo hilo para no bloquear el listener
            threading.Thread(target=realizar_captura_pantalla).start()
    except AttributeError:
        # Ignorar otras teclas que no son especiales (como 'a', 'b', 'c')
        pass
    except Exception as e:
        print(f"Error en el callback de tecla: {e}")


def al_hacer_clic_raton(x, y, button, pressed):
    """Callback que se ejecuta cuando se hace clic con el ratón."""
    global captura_en_cooldown
    try:
        # button.x2 suele ser el botón "Adelante" o "Avanzar página"
        if pressed and button == mouse.Button.x2 and not captura_en_cooldown:
            captura_en_cooldown = True # Marcar como en cooldown
            print("Botón 'Avanzar Página' del ratón presionado! Realizando captura...")
            # Realizar la captura en un nuevo hilo para no bloquear el listener
            threading.Thread(target=realizar_captura_pantalla).start()
    except Exception as e:
        print(f"Error en el callback de clic del ratón: {e}")


def iniciar_escucha_teclado():
    """Inicia el listener para la tecla F2."""
    print("Escuchando la tecla F2... Presiona F2 para capturar la pantalla donde está el cursor.")
    # El listener se ejecuta en su propio hilo, por lo que listener.join() bloqueará
    # el hilo actual (que es el hilo de escucha_teclado).
    with keyboard.Listener(on_press=al_presionar_tecla) as listener:
        listener.join()

def iniciar_escucha_raton():
    """Inicia el listener para el botón 'Avanzar Página' del ratón."""
    print("Escuchando el botón 'Avanzar Página' del ratón...")
    with mouse.Listener(on_click=al_hacer_clic_raton) as listener:
        listener.join()
# --- Lógica de Procesamiento con Gemini ---

class ManejadorCapturas(FileSystemEventHandler):
    """Clase para manejar eventos del sistema de archivos (nuevas capturas)."""
    def __init__(self, modelo_gemini):
        self.modelo_gemini = modelo_gemini
        self.archivos_procesados = set() # Para evitar procesar un archivo múltiples veces

    def on_created(self, evento):
        """Se llama cuando se crea un nuevo archivo en la carpeta monitoreada."""
        if not evento.is_directory and evento.src_path.lower().endswith(('.png', '.jpg', '.jpeg')):
            # Pequeña pausa para asegurar que el archivo se haya escrito completamente
            time.sleep(0.5) 
            
            if evento.src_path in self.archivos_procesados:
                return # Ya procesado o en proceso

            self.archivos_procesados.add(evento.src_path)
            print(f"\nNueva captura detectada: {evento.src_path}")
            self.procesar_con_gemini(evento.src_path)

    def procesar_con_gemini(self, ruta_imagen):
        """Envía la imagen a Gemini y muestra la respuesta."""
        if not self.modelo_gemini:
            print("Error: El modelo Gemini no está configurado. Verifica la API Key.")
            # Intenta recargar la API Key si no estaba disponible al inicio
            global GEMINI_API_KEY
            if not GEMINI_API_KEY:
                load_dotenv() # Carga .env si existe
                GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
            if GEMINI_API_KEY:
                try:
                    genai.configure(api_key=GEMINI_API_KEY)
                    self.modelo_gemini = genai.GenerativeModel(MODELO_GEMINI)
                    print("Modelo Gemini re-inicializado.")
                except Exception as e:
                    print(f"Error al re-inicializar modelo Gemini: {e}")
                    self.archivos_procesados.discard(ruta_imagen) # Permitir reintento
                    return
            else:
                print("API Key de Gemini sigue sin encontrarse.")
                self.archivos_procesados.discard(ruta_imagen) # Permitir reintento
                return

        try:
            print(f"Procesando '{os.path.basename(ruta_imagen)}' con Gemini...")
            imagen = Image.open(ruta_imagen)
            
            respuesta = self.modelo_gemini.generate_content([PROMPT_PARA_GEMINI, imagen])
            
            # Verificar si hubo un bloqueo por seguridad o contenido
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
                return
            
            # Actualizar el ticker con la respuesta de Gemini
            update_ticker(respuesta.text.strip())
        except FileNotFoundError:
            print(f"Error: Archivo de imagen no encontrado durante el procesamiento: {ruta_imagen}")
            self.archivos_procesados.discard(ruta_imagen)
        except Exception as e:
            print(f"Error al procesar con Gemini: {e}")
            # Si fue un error temporal, permitir reintento eliminándolo del set
            if ruta_imagen in self.archivos_procesados:
                 self.archivos_procesados.discard(ruta_imagen)
        finally:
            # Opcional: eliminar la imagen después de procesarla
            # try:
            #     os.remove(ruta_imagen)
            #     print(f"Archivo {ruta_imagen} eliminado después del procesamiento.")
            # except OSError as e_remove:
            #     print(f"Error al eliminar {ruta_imagen}: {e_remove}")
            pass


# --- Ejecución Principal ---
def main():
    global GEMINI_API_KEY # Para que sea accesible globalmente después de cargarla

    # Cargar variables de entorno del archivo .env (si existe)
    load_dotenv()
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    if not GEMINI_API_KEY:
        print("Error Crítico: La API Key de Gemini no está configurada.")
        print("Por favor, crea un archivo .env con la línea: GEMINI_API_KEY='TU_API_KEY'")
        print("O establece la variable de entorno GEMINI_API_KEY.")
        return

    try:
        genai.configure(api_key=GEMINI_API_KEY)
        modelo_gemini = genai.GenerativeModel(MODELO_GEMINI)
        # Prueba rápida para ver si el modelo se carga (opcional)
        # modelo_gemini.generate_content("test") 
        print(f"Modelo Gemini '{MODELO_GEMINI}' inicializado correctamente.")
    except Exception as e:
        print(f"Error al inicializar el modelo Gemini '{MODELO_GEMINI}': {e}")
        print(f"Asegúrate de que tu API key es válida y tienes acceso al modelo '{MODELO_GEMINI}'.")
        print("Puedes probar con 'gemini-1.5-flash-latest' si este modelo no está disponible para tu cuenta.")
        return

    # Crear la carpeta de capturas si no existe
    if not os.path.exists(CAPTURE_FOLDER):
        try:
            os.makedirs(CAPTURE_FOLDER)
            print(f"Carpeta de capturas '{CAPTURE_FOLDER}' creada.")
        except OSError as e:
            print(f"Error al crear la carpeta de capturas '{CAPTURE_FOLDER}': {e}")
            return

    # Evento para coordinar un cierre limpio de la aplicación
    shutdown_event = threading.Event()

    # Inicializar el ticker
    # Pasamos el evento de cierre para que el ícono pueda notificar al hilo principal
    initialize_ticker(shutdown_event)

    # Iniciar el listener de teclado en un hilo separado para no bloquear el programa principal
    hilo_escucha_teclado = threading.Thread(target=iniciar_escucha_teclado, daemon=True)
    hilo_escucha_teclado.start()

    # Iniciar el listener de ratón en un hilo separado
    hilo_escucha_raton = threading.Thread(target=iniciar_escucha_raton, daemon=True)
    hilo_escucha_raton.start()

    print(f"Las capturas se guardarán en la carpeta '{CAPTURE_FOLDER}'.")
    # Iniciar el monitor de la carpeta de capturas
    manejador_eventos = ManejadorCapturas(modelo_gemini=modelo_gemini)
    observador = Observer()
    try:
        observador.schedule(manejador_eventos, CAPTURE_FOLDER, recursive=False)
        observador.start()
        print(f"Monitoreando la carpeta '{CAPTURE_FOLDER}' para nuevas capturas...")
    except Exception as e:
        print(f"Error al iniciar el observador de archivos en '{CAPTURE_FOLDER}': {e}")
        print("Asegúrate de que la ruta es correcta y tienes permisos.")
        return


    try:
        # Mantener el programa principal en ejecución hasta que se señale el cierre
        # desde el ícono de la bandeja del sistema o por Ctrl+C.
        shutdown_event.wait()
    except KeyboardInterrupt:
        print("\nCierre solicitado por el usuario (Ctrl+C)...")
    except Exception as e:
        print(f"Error inesperado: {e}")
    finally:
        print("Iniciando secuencia de apagado...")
        observador.stop()
        observador.join()  # Esperar a que el observador termine limpiamente
        print("Aplicación detenida correctamente.")

if __name__ == "__main__":
    main()
