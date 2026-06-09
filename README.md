# TARCA

Aplicacion de bandeja para capturar pantalla, analizar una pregunta de opcion multiple en la imagen y mostrar la respuesta como letra(s).

## Instalacion

```bat
python -m pip install -r requirements.txt
```

## Configuracion

Copia `.env.example` a `.env` y completa las claves necesarias.

Para usar solo Gemini:

```env
AI_PROVIDER=gemini
CAPTURE_WRITE_DELAY_SECONDS=0.15
IMAGE_MAX_SIZE=1600
IMAGE_JPEG_QUALITY=82
GEMINI_API_KEY=tu_clave_gemini
GEMINI_MODEL=gemini-3.5-flash
GEMINI_FALLBACK_MODELS=gemini-3.1-flash-lite,gemini-2.5-flash,gemini-2.5-flash-lite,gemini-2.5-pro
GEMINI_MAX_OUTPUT_TOKENS=16
GEMINI_THINKING_BUDGET=0
GOOGLE_SEARCH=false
GEMINI_TIMEOUT_SECONDS=20
GEMINI_TRUST_ENV=false
GEMINI_USE_SYSTEM_CERTS=true
```

TARCA no llama a GPT/OpenAI. Si `GEMINI_MODEL` falla, reintenta los modelos gratuitos de `GEMINI_FALLBACK_MODELS` en orden. No se incluye `gemini-3.1-pro-preview` porque requiere facturacion activa.

Mantén `GOOGLE_SEARCH=false` si quieres evitar costes de herramientas externas; la busqueda/grounding tiene limites y tarifas propios.

Para acelerar la respuesta, TARCA redimensiona y comprime la captura antes de enviarla. Sube `IMAGE_MAX_SIZE` a `2000` si alguna pregunta pequena pierde legibilidad.

Los Gems de Gemini se usan desde la app web de Gemini. La API no permite invocar directamente un Gem compartido por enlace, asi que TARCA usa Gemini API con las instrucciones del prompt local.

Si Gemini muestra `CERTIFICATE_VERIFY_FAILED`, TARCA genera un bundle local con certificados de Windows en `.tarca_cache`. Si tu empresa te da un certificado CA concreto, pon su ruta en `GEMINI_CA_BUNDLE`. `GEMINI_TRUST_ENV=false` evita usar proxies rotos definidos en el entorno.

## Uso

Ejecuta `run.bat` y elige el modo de inicio:

- `1`: consola visible con respuestas, errores y mensajes de depuracion.
- `2`: segundo plano sin consola.

Tambien puedes arrancar directamente con `run.bat console` o `run.bat background`.

- `F2`: captura el monitor donde esta el cursor.
- Boton lateral `x2` del raton: tambien dispara una captura.
- Menu de bandeja: activa o desactiva `Ninja Mode` y permite cerrar TARCA.

TARCA solo permite una instancia activa. Si ya esta abierto en la bandeja, un segundo arranque se cerrara para evitar capturas duplicadas.
