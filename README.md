# EVA - Asistente Virtual Personalizado

EVA es un asistente virtual desarrollado en Python como proyecto académico. Su objetivo es permitir que el usuario interactúe con su computadora mediante voz y una interfaz gráfica, ejecutando tareas comunes, respondiendo preguntas y utilizando servicios externos de forma opcional.

---

## Estado actual

Actualmente EVA puede:

- Escuchar comandos por voz.
- Responder por voz usando `pyttsx3`.
- Mostrar la conversación en una interfaz gráfica.
- Abrir y cerrar aplicaciones.
- Controlar Spotify.
- Crear y detener alarmas.
- Crear y gestionar recordatorios.
- Decir la hora y la fecha.
- Realizar búsquedas en Internet.
- Responder preguntas generales mediante Gemini.
- Guardar preferencias de forma local.
- Seguir funcionando aunque Spotify o Gemini no estén configurados.

La prioridad del proyecto es que las funciones principales de EVA no dependan completamente de servicios externos.

---

# Funciones principales

## 1. Reconocimiento de voz

EVA utiliza:

- `SpeechRecognition`
- `PyAudio`

para capturar una sola grabación por pulsación de **Hablar**. El motor principal
es **Faster-Whisper local**, si está instalada la dependencia opcional. Usa el
modelo multilingüe **`small` como único modelo local**, en CPU e `int8`, con idioma
español y tarea de transcripción. No necesita el modelo `base`.

El modelo se carga una sola vez al iniciar EVA en un trabajador propio, sin
bloquear Tkinter, y se reutiliza en todas las escuchas. `PREPARANDO` indica la carga
o calibración y `PROCESANDO` indica el reconocimiento y la ejecución del comando. No hay
escucha permanente ni cambios en el funcionamiento del botón.

Si Whisper aún carga, no está instalado o falla, EVA puede intentar una sola vez
`recognize_google(audio, language="es-PE")` con **la misma grabación**. Este fallback
está habilitado por defecto, **requiere Internet y envía el audio a Google**.
Si ambos motores fallan, se informa del problema sin volver a abrir el micrófono.

Ejemplos:

```text
Eva, abre la calculadora
Eva, ¿qué hora es?
Eva, abre Spotify
Eva, busca inteligencia artificial
```

Whisper procesa el audio localmente: lo convierte en WAV de 16 kHz y 16 bits en
memoria (`BytesIO`), sin guardar grabaciones ni enviarlas a servidores. Se consumen
todos los segmentos, sin recortar la frase por duración o número de tokens. Una
transcripción que supere 60 segundos se cancela y permite usar el fallback.

Al cerrar EVA se cancela la captura pendiente y se cierra el trabajador. Si una
carga o inferencia nativa no termina, se termina ese proceso y se espera su salida
para liberar el modelo. No se instala ningún servicio de Windows.

---

## 2. Respuesta por voz

EVA responde utilizando:

```text
pyttsx3
```

La voz se reproduce de forma local en Windows.

Características actuales:

- No necesita una API externa.
- No consume créditos.
- Funciona sin conexión a Internet una vez generada la respuesta.
- Utiliza un bloqueo de voz para evitar que dos respuestas se reproduzcan al mismo tiempo.
- Actualiza el estado visual `HABLANDO` mientras reproduce audio.

Se probó una integración con ElevenLabs, pero actualmente **no forma parte del proyecto**.

---

## 3. Interfaz gráfica

EVA cuenta con una interfaz desarrollada con `Tkinter`.

La interfaz permite visualizar la conversación entre EVA y el usuario.

Estados principales:

```text
LISTA
PREPARANDO
ESCUCHANDO
PROCESANDO
HABLANDO
```

La conversación se muestra mediante tarjetas o burbujas:

- EVA aparece en un lado.
- El usuario aparece en el lado contrario.

La aplicación utiliza hilos de trabajo y una cola para evitar bloquear la ventana durante tareas como:

- escuchar el micrófono;
- procesar comandos;
- consultar servicios externos;
- reproducir voz.

---

## 4. Control de aplicaciones

EVA puede abrir y cerrar varias aplicaciones de Windows mediante comandos de voz.

Aplicaciones compatibles actualmente:

- Calculadora
- Bloc de notas
- Paint
- Explorador de archivos
- Google Chrome
- Spotify

Ejemplos:

```text
Eva, abre la calculadora
Eva, abre Paint
Eva, abre Chrome
Eva, cierra Chrome
Eva, abre Spotify
```

Algunas aplicaciones del sistema requieren un tratamiento especial para evitar cerrar componentes importantes de Windows.

---

## 5. Spotify

EVA puede controlar Spotify cuando el usuario configura su propia cuenta.

Funciones implementadas:

- Abrir Spotify.
- Detectar dispositivos disponibles.
- Reproducir canciones por nombre.
- Buscar canciones por artista.
- Reanudar la reproducción.
- Pasar a la siguiente canción.
- Agregar canciones a la cola.
- Seleccionar un dispositivo disponible.

Ejemplos:

```text
Eva, reproduce Numb
Eva, reproduce In the End de Linkin Park
Eva, siguiente canción
Eva, continúa la música
```

### Spotify es opcional

Si Spotify no está configurado, EVA sigue funcionando normalmente.

La configuración se mantiene fuera del repositorio para evitar exponer datos sensibles.

---

## 6. Ajustes de Spotify

La interfaz incluye una sección de configuración de Spotify.

Permite:

- ingresar el Client ID;
- configurar el Redirect URI;
- guardar la configuración;
- conectar Spotify;
- desconectar Spotify;
- ver el estado de conexión.

La configuración local se almacena en Windows fuera del repositorio, utilizando una ruta similar a:

```text
%LOCALAPPDATA%\EVA\
```

Las sesiones sensibles se mantienen separadas de los archivos públicos del proyecto.

---

## 7. Gemini

EVA puede utilizar Gemini como sistema opcional para responder preguntas generales.

Gemini se utiliza como último recurso, después de comprobar si el usuario pidió una función local.

Flujo general:

```text
Comando del usuario
        ↓
¿Es una función local de EVA?
        ↓
Sí → Ejecutar función local
No  → Consultar Gemini
```

Esto evita que Gemini interfiera con funciones como:

- abrir aplicaciones;
- Spotify;
- alarmas;
- recordatorios;
- búsquedas;
- fecha y hora.

### Gemini es opcional

Si Gemini:

- no está configurado;
- no tiene API key;
- alcanza su cuota;
- falla;
- no tiene conexión;

EVA continúa funcionando con sus funciones locales.

---

## 8. Configuración de Gemini

Gemini puede configurarse desde la interfaz de Ajustes.

La API key:

- no se guarda directamente en el código;
- no debe subirse a GitHub;
- se almacena localmente;
- puede protegerse mediante Windows DPAPI.

La sección de Ajustes permite:

- guardar la API key;
- probar la conexión;
- desconectar Gemini;
- visualizar su estado.

---

## 9. Manejo de errores y cuota de Gemini

EVA puede detectar errores relacionados con límites de uso, por ejemplo:

```text
HTTP 429
```

Cuando Gemini alcanza un límite:

- muestra un mensaje seguro;
- no muestra la API key;
- no muestra tokens;
- no bloquea el resto de EVA;
- evita realizar peticiones repetitivas inmediatamente.

---

## 10. Alarmas

EVA puede crear alarmas mediante comandos de voz.

Ejemplos:

```text
Eva, pon una alarma a las 3:30 de la tarde
Eva, pon una alarma a las 7 de la mañana
```

Características:

- funcionan en segundo plano;
- utilizan sonido de Windows;
- interpretan horas de mañana, tarde y noche;
- pueden detenerse mediante comando.

---

## 11. Recordatorios

EVA permite crear recordatorios mediante voz.

Ejemplos:

```text
Eva, recuérdame estudiar en 10 minutos
Eva, recuérdame hacer mi tarea dentro de una hora
```

Los recordatorios se almacenan localmente en:

```text
recordatorios.json
```

El archivo se crea automáticamente cuando es necesario.

También se pueden eliminar recordatorios.

---

## 12. Hora y fecha

EVA puede responder preguntas relacionadas con la hora y la fecha.

Ejemplos:

```text
Eva, ¿qué hora es?
Eva, dime la fecha
Eva, ¿qué día es hoy?
```

---

## 13. Búsquedas en Internet

EVA puede realizar búsquedas utilizando el navegador.

Ejemplo:

```text
Eva, busca inteligencia artificial
```

La consulta se abre automáticamente en el navegador predeterminado.

---

## 14. Preferencias

EVA puede almacenar información local del usuario mediante:

```text
preferencias.json
```

El archivo se genera automáticamente si no existe.

Esta estructura está preparada para permitir una personalización mayor en futuras versiones.

---

# Arquitectura general

```text
Usuario
  ↓
Micrófono
  ↓
SpeechRecognition + PyAudio
  ↓
Texto reconocido
  ↓
Procesamiento del comando
  ↓
┌──────────────────────────────┐
│ Funciones locales            │
│                              │
│ Aplicaciones                 │
│ Spotify                      │
│ Alarmas                      │
│ Recordatorios                │
│ Hora y fecha                 │
│ Navegador                    │
└──────────────────────────────┘
  ↓
Si no corresponde a una función local
  ↓
Gemini (opcional)
  ↓
Respuesta
  ↓
Interfaz gráfica
  ↓
pyttsx3
  ↓
Altavoces
```

---

# Estructura principal del proyecto

La estructura puede cambiar a medida que EVA evolucione.

```text
Proyecto_EVA/
│
├── main.py
├── interfaz.py
├── whisper_control.py
│
├── spotify_control.py
├── spotify_config.py
├── spotify_sesion.py
│
├── gemini_control.py
├── gemini_config.py
│
├── alarmas.py
├── recordatorios.py
├── tiempo_eva.py
│
├── config.py
├── config_ejemplo.py
│
├── preferencias.json
├── recordatorios.json
│
├── requirements.txt
├── requirements-whisper.txt
├── .gitignore
└── README.md
```

---

# Tecnologías utilizadas

## Lenguaje

```text
Python 3.13
```

## Principales librerías y tecnologías

- Tkinter
- SpeechRecognition
- PyAudio
- pyttsx3
- Spotipy
- Google GenAI
- threading
- webbrowser
- winsound
- JSON
- Windows DPAPI
- Git
- GitHub

---

# Instalación

## 1. Clonar el repositorio

```bash
git clone https://github.com/Jeffzx-404/EVA-Asistente-Virtual.git
```

Entrar en la carpeta:

```bash
cd EVA-Asistente-Virtual
```

---

## 2. Crear el entorno virtual

En Windows:

```powershell
py -3.13 -m venv .venv
```

Activarlo:

```powershell
.\.venv\Scripts\Activate.ps1
```

---

## 3. Instalar dependencias

```powershell
python -m pip install -r requirements.txt
```

---

## 4. Ejecutar EVA

```powershell
python main.py
```

---

## Reconocimiento local opcional con Whisper

Dentro del entorno virtual de Python 3.13, después de instalar `requirements.txt`:

```powershell
python -m pip install -r requirements-whisper.txt
python main.py
```

La primera carga descarga los pesos de `small` desde Hugging Face; necesita Internet
y puede tardar según la conexión. Se guardan fuera del repositorio, en
`%LOCALAPPDATA%\EVA\whisper`. En los siguientes inicios se busca primero la copia
local, sin consultar Internet si ya está disponible. No se añaden modelos a Git.
Si se cierra EVA durante la descarga, se cancela el trabajador; el siguiente inicio
intentará cargar la caché disponible. Si la descarga quedó incompleta, puede ser
necesaria conexión para completarla.

### Small automático

No hay selector de modelos: EVA utiliza siempre Faster-Whisper `small`
multilingüe. La antigua variable `EVA_WHISPER_MODELO` se ignora, incluso si aún
tiene el valor `base`. No necesitas definir ninguna variable para elegir small.
Con EVA cerrada, inicia desde PowerShell:

```powershell
.\.venv\Scripts\python.exe main.py
```

La consola debe mostrar:

```text
[Whisper] Modelo: small (multilingue, cpu, int8)
```

En la conversación verás `Cargando Whisper local (small)` y después
`Whisper local listo (small)`. Espera al segundo mensaje y pulsa **Hablar**.
Para comprobar el reconocimiento local sin Google, inicia con
`$env:EVA_GOOGLE_FALLBACK = "0"` y prueba «Eva, qué hora es».
La carga sigue siendo asíncrona y el mismo modelo se reutiliza durante la sesión.

Small se descarga automáticamente cuando falta su copia completa y hay Internet.
La siguiente sesión utiliza esa copia offline. Si small no está disponible y no
se puede descargar, EVA conserva el fallback opcional de Google (requiere Internet)
o informa del fallo si está desactivado. Nunca intenta cargar ni descargar base.

### Caché y limpieza opcional de base

La caché existente se conserva sin moverla, convertirla ni borrarla. Inspección
local del 27/10/2026: Hugging Face mantiene estos directorios independientes en
`%LOCALAPPDATA%\EVA\whisper`:

```text
models--Systran--faster-whisper-base\
models--Systran--faster-whisper-small\
.locks\models--Systran--faster-whisper-base\
.locks\models--Systran--faster-whisper-small\
CACHEDIR.TAG
```

Los **seis archivos exclusivos de la carpeta base**, con rutas relativas a
`models--Systran--faster-whisper-base`, son:

| Archivo | Bytes |
| --- | ---: |
| `refs/main` | 40 |
| `snapshots/ebe41f70d5b6dfa9166e2c581c45c9c0cfc57b66/config.json` | 2 309 |
| `snapshots/ebe41f70d5b6dfa9166e2c581c45c9c0cfc57b66/model.bin` | 145 217 532 |
| `snapshots/ebe41f70d5b6dfa9166e2c581c45c9c0cfc57b66/tokenizer.json` | 2 203 239 |
| `snapshots/ebe41f70d5b6dfa9166e2c581c45c9c0cfc57b66/vocabulary.txt` | 459 861 |
| `trees/ebe41f70d5b6dfa9166e2c581c45c9c0cfc57b66.json` | 867 |

Total: **147 883 848 bytes (aproximadamente 141 MiB)**. `blobs` y la carpeta de
bloqueos de base están vacías. No se encontraron enlaces simbólicos; tokenizer
y vocabulary coinciden en contenido con los de small, pero se comprobó que son
archivos independientes, sin enlaces duros compartidos.

Puedes eliminar únicamente el repositorio base y su subcarpeta de bloqueos.
Conserva el repositorio small, sus bloqueos, el directorio padre `.locks` y
`CACHEDIR.TAG`. Con EVA y sus pruebas cerradas, este comando de PowerShell verifica
las rutas y **solo muestra una vista previa**; no se ha ejecutado ningún borrado:

```powershell
$cacheWhisper = (Resolve-Path -LiteralPath (Join-Path $env:LOCALAPPDATA 'EVA\whisper')).Path
$objetivosBase = @(
    (Join-Path $cacheWhisper 'models--Systran--faster-whisper-base'),
    (Join-Path $cacheWhisper '.locks\models--Systran--faster-whisper-base')
)
foreach ($objetivoBase in $objetivosBase) {
    if (-not (Test-Path -LiteralPath $objetivoBase)) { continue }
    $rutaBase = (Resolve-Path -LiteralPath $objetivoBase).Path
    if ($rutaBase -ne $objetivoBase -or -not $rutaBase.StartsWith($cacheWhisper + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw 'Ruta inesperada; se cancela la limpieza.'
    }
    $elementosBase = @(Get-Item -LiteralPath $rutaBase) + @(Get-ChildItem -LiteralPath $rutaBase -Recurse -Force)
    if ($elementosBase | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint }) {
        throw 'Se encontraron enlaces; revisar antes de borrar.'
    }
    Remove-Item -LiteralPath $rutaBase -Recurse -Force -WhatIf
}
```

Revisa que la vista previa mencione únicamente las dos rutas de base. Para borrar
realmente esas carpetas, repite el bloque quitando **solo** `-WhatIf`.
No uses comodines ni borres la raíz `whisper`.

### Medir small

Para el análisis de latencia por etapas y las comparaciones realizadas, consulta
[el informe de latencia](tests/INFORME_LATENCIA.md). No se han medido tu micrófono
ni los tiempos reales de apertura de aplicaciones o reproducción de voz.

Activa el diagnóstico antes de abrir EVA:

```powershell
$env:EVA_DIAGNOSTICO_VOZ = "1"
$env:EVA_GOOGLE_FALLBACK = "0" # Aislar Whisper durante la medición
$env:EVA_PAUSA_VOZ = "0.8"     # Valor conservador predeterminado
.\.venv\Scripts\python.exe main.py
```

Los tiempos usan `time.perf_counter()` y distinguen:

| Métrica | Qué mide |
| --- | --- |
| `preparacion_microfono_s` / `calibracion_s` | Apertura y calibración / solo calibración. La segunda está incluida en la primera. |
| `captura_listen_s` | Espera hasta empezar a hablar, voz y silencio final; termina al devolver `listen()`. |
| `listen_a_transcribir_s` | Intervalo posterior a `listen()` hasta preparar la llamada al reconocedor; incluye liberación del micrófono y diagnóstico. |
| `conversion_audio_s` / `preparacion_envio_s` | Una conversión a WAV 16 kHz/16 bits / codificación y envío al trabajador. |
| `preprocesado_whisper_s` | Decodificación WAV, VAD y extracción de características. |
| `inferencia_s` | Consumo completo de los segmentos, incluida la generación del texto. |
| `normalizacion_deteccion_s` | Tiempo del procesador excluyendo llamadas directas a acciones o respuestas. |
| `accion_local_<funcion>_s` | Duración de cada acción local observada, sin modificar su implementación. |
| `captura_a_comando_s` | Desde que `listen()` devuelve audio hasta entrar en la primera acción o respuesta. |

`transcripcion_s` incluye preprocesado e inferencia; `transcripcion_total_s` añade
preparación e intercambio entre procesos. No sumes métricas que se incluyen entre
sí. `audio_s` y `audio_despues_vad_s` son duraciones del audio, no tiempos de CPU.
`fallback_google_s` permite distinguir un intento de red de la inferencia local.
`numero_transcripcion=1` identifica el primer intento de inferencia del trabajador;
los números siguientes identifican intentos posteriores sobre el mismo modelo.
Un primer intento vacío o fallido no garantiza que toda la inicialización de
inferencia se haya completado. La carga del modelo se sigue midiendo por separado.

El perfil de comandos solo se instala temporalmente en el hilo de voz cuando hay
diagnóstico. Registra nombres y duraciones, nunca argumentos. Las respuestas
directas se etiquetan `respuesta_voz_hablar_s`; servicios externos, por separado.
Si una acción local llama internamente a `hablar`, su duración incluye esa voz:
no es tiempo puro del sistema operativo. No se modifica pyttsx3. Un perfilador
externo ya instalado tiene prioridad; en ese caso se omiten estas métricas de
acciones. La secuencia visual es **PREPARANDO → ESCUCHANDO → PROCESANDO → HABLANDO
→ LISTA**, con una sola fase de procesamiento por captura y prioridad de voz.

Para comparar **una misma toma** de tu micrófono sin guardar audio ni ejecutar órdenes:

```powershell
.\.venv\Scripts\python.exe tests/comparar_microfono_voz.py --caso 1 --repeticiones 5
```

Repite con casos `1` a `8`, `rapida`, `pausas`, `larga`, `silencio` y `ruido`.
La herramienta captura una referencia con pausa de 1.5 s y luego la reproduce
en memoria para comparar 0.8, 0.7 y 0.65; no cambia el ajuste de EVA. Distingue el
tiempo real de captura de la duración simulada del audio. Muestra la primera
transcripción tras cargar small por separado, excluida de las medianas. Después
repite cada WAV ya preparado cinco veces con orden rotativo (mínimo tres con
`--repeticiones`). Informa medianas, estabilidad del texto y si los WAV son
idénticos. Si son idénticos, diferencias de inferencia no se deben al umbral de
pausa. No guarda la grabación ni las transcripciones en disco.
En ruido, utiliza un
ambiente moderado y constante; compara principio, final, nombres, horas y textos
de recordatorio. No habla por ti ni puede validar tu pronunciación automáticamente.

En la aplicación, `EVA_PAUSA_VOZ` acepta 0.8, 0.7 y 0.65; cualquier otro valor usa
0.8. Solo cambia esa variable para comparar el final de frase: deja el VAD igual.
No se recomienda reducirla sin superar las pruebas con tu voz. Conserva
`non_speaking_duration=0.5`, `phrase_threshold=0.3`, energía inicial 300 y ajuste
dinámico. La calibración sigue durando un segundo; `timeout=None` y
`phrase_time_limit=None` evitan limitar comandos largos. En silencio la captura
real espera hasta detectar voz o cerrar EVA; la herramienta manual usa un timeout
de 8 s exclusivamente para poder finalizar ese caso de prueba.

Para mostrar mediciones durante el uso de EVA, antes de iniciarla:

```powershell
$env:EVA_WHISPER_MEDIR = "1"
.\.venv\Scripts\python.exe main.py
```

Las mediciones están desactivadas por defecto. También se activan con
`EVA_DIAGNOSTICO_VOZ="1"`; para apagarlas, ambas variables deben estar en `"0"`.
Las métricas imprimen números y etiquetas, sin grabar audio ni argumentos de acciones.
El diagnóstico de texto existente muestra transcripciones solo en consola y omite
posibles credenciales:

- `carga_s`: importación de dependencias, búsqueda de caché y carga del modelo en
  el trabajador. Incluye la descarga si faltan archivos.
- `arranque_s`: desde el lanzamiento asíncrono hasta recibir el estado listo;
  incluye además el inicio del proceso y la comunicación.
- `transcripcion_s`: decodificación del WAV y consumo de todos los segmentos en
  el trabajador, sin modificar los parámetros actuales de transcripción.
- `transcripcion_total_s`: tiempo observado por EVA, incluyendo conversión del
  audio e intercambio entre procesos.
- `captura_a_respuesta_s`: desde que termina `listen()` hasta la primera llamada
  a `hablar()` en ese hilo; incluye reconocimiento, fallback si se usa y
  procesamiento del comando. Termina **antes de actualizar la interfaz o
  reproducir pyttsx3**; no mide cuándo se oye la voz. Si no hay respuesta hablada,
  no se imprime esta métrica.
- `ram_mb`: RAM residente aproximada del trabajador en MiB, muestreada al acabar
  la carga y cada transcripción. No es el total de EVA ni el pico de memoria.
  Se consulta mediante la [API de Windows](https://learn.microsoft.com/en-us/windows/win32/psapi/process-memory-usage-information)
  con `ctypes`, sin dependencias adicionales. Si no está disponible, se omite.

Medición reproducible de small, con las doce frases de prueba (con y sin EVA),
sintetizadas una sola vez en memoria:

```powershell
.\.venv\Scripts\python.exe tests/comparar_modelos_whisper.py --descargar-modelo --salida medicion_small.json
```

El script conserva su nombre por compatibilidad, pero ahora mide únicamente small;
no necesita base. `--descargar-modelo` prepara small antes de cronometrar (el antiguo
`--descargar-modelos` sigue siendo un alias y también prepara solo small). Si ya
está completo, omite esa opción. La medición bloquea la red del trabajador y
verifica por SHA-256 que la caché no cambie durante la fase offline. Añade
`--repeticiones 3` para repetir las mismas muestras sin recargar el modelo.
`tests/resultados_comparacion_whisper.json` se conserva como resultado histórico
de base/small; no describe la configuración actual ni se utiliza para cargar modelos.

El JSON contiene tiempos individuales, RAM, transcripciones sintéticas y si cada
orden se resolvió localmente. La latencia hasta respuesta de esta medición es
**simulada**: ejecuta el procesador real con aplicaciones, alarmas, recordatorios,
Gemini y voz sustituidos por dobles de prueba. No mide la apertura real de apps ni
la reproducción de voz. La primera inferencia puede tardar más por inicialización;
compara también las muestras posteriores. No es una evaluación con micrófono real.

El archivo opcional limita PyAV a una versión anterior a 19 para evitar la
[incompatibilidad de lectura de audio con Faster-Whisper 1.2.1](https://github.com/SYSTRAN/faster-whisper/issues/1589).
Si ya tenías Whisper instalado, vuelve a ejecutar la instalación indicada arriba.

Para impedir que el fallback envíe audio a Google, antes de iniciar EVA:

```powershell
$env:EVA_GOOGLE_FALLBACK = "0"
python main.py
```

Con el modelo ya descargado, Whisper reconoce comandos en español sin Internet.
Los servicios externos, como Spotify o Gemini, conservan sus propios requisitos
de conexión. Para volver a permitir el fallback, usa
`$env:EVA_GOOGLE_FALLBACK = "1"`. No hace falta editar `config.py`.

Si no instalas `requirements-whisper.txt`, EVA sigue funcionando con Google cuando
el fallback está habilitado. Si también está deshabilitado, mostrará un mensaje
claro al intentar hablar; puedes seguir escribiendo comandos.

Pruebas automáticas sin micrófono ni descarga (incluyen trabajadores simulados):

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
python -m py_compile main.py interfaz.py whisper_control.py comandos_voz.py metricas_voz.py
git diff --check
```

Prueba adicional con modelo real, Tkinter y voz española sintética de Windows,
sin micrófono ni archivos de audio. `--descargar-modelo` prepara la caché; la fase
de reconocimiento bloquea las conexiones de red del trabajador:

```powershell
python tests/comprobar_whisper_local.py --descargar-modelo
```

Si el modelo ya está en caché, omite `--descargar-modelo`.

En la comprobación local inicial del 27/10/2026 (previa a instrumentar la latencia), small resolvió **11 de 12 comandos**:
el audio sintético «dime la hora» se transcribió como «Dímela ahora», por lo que
esta prueba adicional terminó con una aserción fallida. Es la misma limitación
registrada para small en el JSON histórico; «Eva, dime la hora» sí funcionó.
La carga offline, la respuesta de Tkinter durante el trabajo, el silencio y el
cierre del trabajador funcionaron. Las 40 pruebas automáticas con dobles pasaron.
Se mantienen los parámetros solicitados y la prueba estricta para hacer visible
esta limitación; falta comprobar la precisión con tu voz y micrófono.

### Precisión y diagnóstico temporal

Se mantiene small multilingüe en CPU/int8, `language="es"`, `task="transcribe"`,
`beam_size=5`, `temperature=0` y `condition_on_previous_text=False`. La única pista
añadida al decodificador es un vocabulario corto mediante `hotwords`: EVA, hora,
calculadora, alarma y recuérdame. No se impone una frase ni se cambia el modelo.
En la comparación con audio sintético, incluir «recuérdame» ayudó a evitar su
separación como «recuerda me». El procesador también admite «recordame» y
«recuerda me» únicamente al principio de una orden de recordatorio.

La calibración del micrófono sigue durando un segundo: permanece en silencio
mientras aparece `PREPARANDO` y habla cuando cambie a `ESCUCHANDO`. La captura no
tiene un límite de duración de frase. Se conservan el umbral de pausa de
SpeechRecognition y el VAD de Whisper (700 ms de silencio y 400 ms de margen),
para evaluar la pista de vocabulario sin mezclar cambios en varios parámetros.

La detección de hora ignora mayúsculas, tildes y puntuación; también acepta
«que ahora es», «qué oras» y «hora actual». Se exige una consulta completa para no confundir
«recuérdame preguntar qué hora es en una hora» con una consulta de hora local.
La eliminación del vocativo EVA respeta palabras como «llevar» y «evaluar».
Los textos originales y los horarios como `05:30` se conservan para su procesamiento.

Para ver temporalmente el resultado de Whisper y las rutas de hora, calculadora,
alarmas, recordatorios o consulta general en la consola:

```powershell
$env:EVA_DIAGNOSTICO_VOZ = "1"
python main.py
```

Ejemplo: `whisper: 'que ahora es'` seguido de `intencion: 'hora_local'`.
El diagnóstico está desactivado por defecto, no añade mensajes a la interfaz,
no guarda audio ni crea archivos de registro. Omite textos que parezcan contener
credenciales. Para desactivarlo, cierra EVA y usa
`$env:EVA_DIAGNOSTICO_VOZ = "0"` antes del siguiente inicio.

La prueba sintética comprueba doce comandos (con y sin EVA), que se resuelvan
localmente sin llamar a Gemini, y que el silencio no produzca un comando. No
sustituye una prueba con tu voz y tu micrófono.

Para una comprobación con micrófono: inicia EVA con `EVA_GOOGLE_FALLBACK=0`, espera
el mensaje «Whisper local listo», desconecta Internet y prueba varias veces «Eva, qué hora es» y «Eva, abre
la calculadora». Comprueba también que la ventana responde durante la carga y que
no queda un trabajador de `whisper_control.py` tras cerrarla durante una carga o
transcripción. Las pruebas automáticas no validan el micrófono físico.

Referencia: [documentación oficial de Faster-Whisper](https://github.com/SYSTRAN/faster-whisper).

---

# Configuración de servicios externos

EVA está diseñada para funcionar aunque los servicios externos no estén configurados.

## Spotify

Cada usuario debe utilizar su propia configuración de Spotify.

No deben publicarse:

- tokens;
- sesiones;
- Client Secret;
- credenciales privadas.

## Gemini

Cada usuario debe utilizar su propia API key.

Nunca debe subirse una API key a GitHub.

---

# Seguridad

Los siguientes datos no deben incluirse en el repositorio:

```text
API keys
Client secrets
Tokens OAuth
Sesiones
Contraseñas
Credenciales
Archivos privados de configuración
```

El archivo `.gitignore` se utiliza para excluir:

- `.venv/`;
- cachés;
- configuraciones locales;
- archivos temporales;
- credenciales;
- sesiones;
- archivos generados localmente.

---

# Control de versiones

El proyecto utiliza Git y GitHub.

Flujo de trabajo:

```text
main
 ↓
rama de desarrollo
 ↓
pruebas
 ↓
commit
 ↓
push
 ↓
Pull Request
 ↓
merge
```

También se utilizan etiquetas para conservar versiones estables.

Entre las etiquetas creadas durante el desarrollo se encuentran:

```text
v1.1-estable
v1.2-estable
v1.3-estable
v1.4-estable
```

---

# Objetivo académico

EVA fue desarrollada como proyecto de Fundamentos de Programación.

Su objetivo es crear un asistente virtual personalizado capaz de:

- responder a su nombre;
- reconocer saludos y despedidas;
- recibir comandos por voz;
- abrir y cerrar aplicaciones;
- reproducir música;
- crear alarmas;
- crear recordatorios;
- realizar búsquedas;
- responder preguntas;
- adaptarse gradualmente a las preferencias del usuario.

---

# Posibles mejoras futuras

Entre las siguientes mejoras planteadas se encuentran:

- mejorar la calidad del reconocimiento de voz;
- mejorar la voz local;
- ampliar las preferencias del usuario;
- agregar más aplicaciones compatibles;
- mejorar la gestión visual de alarmas;
- mejorar la gestión visual de recordatorios;
- ampliar la sección de Ajustes;
- permitir una configuración más sencilla para otros usuarios;
- preparar una versión instalable de EVA;
- mejorar la documentación del proyecto.

---

# Importante

EVA es un proyecto educativo.

Los servicios externos utilizados pueden tener:

- límites de uso;
- cuotas;
- cambios de disponibilidad;
- requisitos propios de cada proveedor.

Por esta razón, EVA intenta mantener sus funciones principales disponibles incluso cuando un servicio externo falla o no está configurado.

---

# Autores:

🧑‍💻 Integrantes
- Bob El Constructor
- Angel K-Brito
- Junior Adicto a la Coca-Cola
- Jose Decimo Piso
- Rudy Stickers Turbios


Proyecto académico de **TECSUP**.

---

# Licencia

Proyecto desarrollado con fines educativos.
