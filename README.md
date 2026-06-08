# TARCA

Aplicacion de bandeja para capturar pantalla, analizar una pregunta de opcion multiple en la imagen y mostrar la respuesta como letra(s).

## Instalacion

```bat
python -m pip install -r requirements.txt
```

## Configuracion

Copia `.env.example` a `.env` y completa las claves necesarias.

Para usar Gemini como proveedor principal y GPT como respaldo:

```env
AI_PROVIDER=auto
CAPTURE_WRITE_DELAY_SECONDS=0.15
IMAGE_MAX_SIZE=1600
IMAGE_JPEG_QUALITY=82
GEMINI_API_KEY=tu_clave_gemini
GEMINI_MODEL=gemini-2.5-flash
GEMINI_MAX_OUTPUT_TOKENS=16
GEMINI_THINKING_BUDGET=0
GOOGLE_SEARCH=false
GEMINI_TIMEOUT_SECONDS=20
GEMINI_TRUST_ENV=false
GEMINI_USE_SYSTEM_CERTS=true
OPENAI_FALLBACK=true
OPENAI_API_KEY=tu_clave_openai
OPENAI_MODEL=gpt-5.4-mini
OPENAI_MAX_OUTPUT_TOKENS=16
OPENAI_TIMEOUT_SECONDS=30
OPENAI_WEB_SEARCH=false
OPENAI_TRUST_ENV=false
OPENAI_USE_SYSTEM_CERTS=true
```

Con `AI_PROVIDER=auto`, la app usa Gemini si existe `GEMINI_API_KEY`; si Gemini no esta disponible y `OPENAI_FALLBACK=true`, reintenta con GPT.

Para acelerar la respuesta, TARCA redimensiona y comprime la captura antes de enviarla. Sube `IMAGE_MAX_SIZE` a `2000` si alguna pregunta pequena pierde legibilidad.

Los Gems de Gemini se usan desde la app web de Gemini. La API no permite invocar directamente un Gem compartido por enlace, asi que TARCA usa Gemini API con las instrucciones del prompt local.

Si Gemini muestra `CERTIFICATE_VERIFY_FAILED`, TARCA genera un bundle local con certificados de Windows en `.tarca_cache`. Si tu empresa te da un certificado CA concreto, pon su ruta en `GEMINI_CA_BUNDLE`. `GEMINI_TRUST_ENV=false` evita usar proxies rotos definidos en el entorno.

Si ves `Connection error` en OpenAI:

- `OPENAI_TRUST_ENV=false` evita usar proxies rotos definidos en el entorno.
- `OPENAI_USE_SYSTEM_CERTS=true` usa certificados del sistema con el paquete `truststore`.
- Si tu empresa te da un certificado CA concreto, pon su ruta en `OPENAI_CA_BUNDLE`.

## Uso

Ejecuta `run.bat` y elige el modo de inicio:

- `1`: consola visible con respuestas, errores y mensajes de depuracion.
- `2`: segundo plano sin consola.

Tambien puedes arrancar directamente con `run.bat console` o `run.bat background`.

- `F2`: captura el monitor donde esta el cursor.
- Boton lateral `x2` del raton: tambien dispara una captura.
- Menu de bandeja: activa o desactiva `Ninja Mode` y permite cerrar TARCA.

TARCA solo permite una instancia activa. Si ya esta abierto en la bandeja, un segundo arranque se cerrara para evitar capturas duplicadas.
