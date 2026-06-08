# TARCA

Aplicacion de bandeja para capturar pantalla, analizar una pregunta de opcion multiple en la imagen y mostrar la respuesta como letra(s).

## Instalacion

```bat
python -m pip install -r requirements.txt
```

## Configuracion

Copia `.env.example` a `.env` y completa las claves necesarias.

Para usar la API de GPT/OpenAI:

```env
AI_PROVIDER=openai
OPENAI_API_KEY=tu_clave
OPENAI_MODEL=gpt-5.4-mini
OPENAI_MAX_OUTPUT_TOKENS=128
OPENAI_TIMEOUT_SECONDS=60
OPENAI_WEB_SEARCH=false
OPENAI_TRUST_ENV=false
OPENAI_USE_SYSTEM_CERTS=true
```

Si `AI_PROVIDER` no esta definido, la app usa OpenAI cuando existe `OPENAI_API_KEY`; si no, intenta usar Gemini.

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
