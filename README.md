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

para capturar el audio del micrófono y convertirlo en texto.

Actualmente el reconocimiento se realiza mediante:

```python
recognize_google(audio, language="es-PE")
```

Esto permite que EVA reconozca comandos hablados en español.

Ejemplos:

```text
Eva, abre la calculadora
Eva, ¿qué hora es?
Eva, abre Spotify
Eva, busca inteligencia artificial
```

> El reconocimiento de voz actual requiere conexión a Internet.

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
