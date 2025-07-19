import threading
from pystray import Icon, MenuItem
from PIL import Image, ImageDraw, ImageFont

# --- Variables globales ---
tray_icon = None
shutdown_event_global = None
last_known_answer = "" # Variable para guardar la última respuesta

# --- Funciones del ícono de la bandeja del sistema ---

def create_text_icon(text):
    """
    Crea dinámicamente una imagen de ícono que contiene el texto proporcionado.
    """
    # Usar una fuente común de Windows. Si no se encuentra, usa la fuente por defecto.
    try:
        # Usar una fuente clara y de tamaño adecuado para la barra de tareas
        font = ImageFont.truetype("segoeui.ttf", size=18)
    except IOError:
        font = ImageFont.load_default()

    # Crear un lienzo temporal para medir el texto sin crearlo
    temp_image = Image.new("RGBA", (1, 1))
    temp_draw = ImageDraw.Draw(temp_image)
    
    # Calcular el bounding box del texto para obtener su ancho real
    _, _, text_width, text_height = temp_draw.textbbox((0, 0), text, font=font)
    
    # Definir la altura del ícono y el padding
    icon_height = 24
    padding = 8 # 4px a cada lado

    # Crear la imagen final con fondo transparente
    image = Image.new("RGBA", (text_width + padding, icon_height), (0, 0, 0, 0))
    dc = ImageDraw.Draw(image)

    # Dibujar el texto con un contorno negro para máxima visibilidad en cualquier tema de barra de tareas.
    # Se centra verticalmente.
    y_pos = (icon_height - text_height) / 2
    dc.text((padding / 2, y_pos), text, font=font, fill="white", stroke_width=1, stroke_fill="black")

    return image

def exit_action():
    """Notifica al hilo principal que debe terminar y detiene el ícono."""
    if shutdown_event_global:
        shutdown_event_global.set()
    if tray_icon:
        tray_icon.stop()

def run_widget():
    """Función de destino para el hilo. Crea y ejecuta el ícono."""
    global tray_icon
    
    # Crear un ícono inicial
    initial_icon = create_text_icon("TARCA")
    
    # Definir el menú del clic derecho
    menu = (MenuItem('Exit TARCA', exit_action),)
    
    # Crear y ejecutar el ícono de pystray
    tray_icon = Icon('TARCA', initial_icon, "TARCA: Listo para analizar.", menu)
    tray_icon.run()

# --- Funciones públicas para controlar el ticker ---

def _set_icon_state(text, title):
    """Función interna para actualizar el ícono y el tooltip."""
    if tray_icon:
        new_icon = create_text_icon(text)
        tray_icon.icon = new_icon
        tray_icon.title = title

def show_processing_state():
    """Muestra un ícono de 'procesando' en la bandeja del sistema."""
    if last_known_answer:
        # Si hay una respuesta anterior, la muestra con un punto
        processing_text = f"{last_known_answer}."
    else:
        # Si es la primera vez o se reseteó, muestra "..."
        processing_text = "..."
    _set_icon_state(processing_text, "Procesando con IA...")

def reset_to_default_state():
    """Restaura el ícono al estado inicial."""
    global last_known_answer
    _set_icon_state("TARCA", "TARCA: Listo para analizar.")
    last_known_answer = "" # Limpiar la última respuesta conocida

def initialize_ticker(shutdown_event):
    """Inicializa y ejecuta el widget en un hilo separado."""
    global shutdown_event_global
    shutdown_event_global = shutdown_event
    
    icon_thread = threading.Thread(target=run_widget, daemon=True)
    icon_thread.start()

def update_ticker(data):
    """Función pública para actualizar el texto del widget desde el hilo principal."""
    global last_known_answer # Necesario para modificar la variable global
    if tray_icon:
        clean_data = data.strip()

        # Si la respuesta está vacía, no hacer nada para evitar un ícono invisible.
        if not clean_data:
            print("Respuesta de IA vacía, se restaura el ícono.")
            reset_to_default_state()
            # last_known_answer ya se limpia en reset_to_default_state()
            return

        # Generar un nuevo ícono con el texto de la respuesta
        _set_icon_state(clean_data, f"Respuesta: {clean_data}")
        last_known_answer = clean_data # Guardar la respuesta actual para el próximo procesamiento
