# 🤖 EVA - Asistente Virtual Personalizado

EVA es un asistente virtual desarrollado en **Python** capaz de interactuar con el usuario mediante comandos de voz y texto.

Este proyecto fue desarrollado como parte del curso de Fundamentos de Programación.

## 🧑‍💻 Integrantes

- Bob el constructor
- Angel K-Brito
- Junior el que le gusta la Coca-Cola
- Jose le gustan las malcriadas
- Rudy vive en la chacra


## 🚀 Funciones actuales

Actualmente EVA puede:

- 🎤 Reconocer comandos de voz.
- 🔊 Responder mediante voz.
- 💬 Recibir comandos desde una interfaz gráfica.
- 💻 Abrir y cerrar aplicaciones de Windows.
- 🌐 Realizar búsquedas en Internet.
- 🌐 Abrir páginas web.
- 🎵 Buscar canciones en Spotify.
- ▶️ Reproducir canciones en Spotify.
- ⏸️ Pausar y continuar la música.
- ⏭️ Cambiar de canción.
- 🔊 Controlar el volumen de Spotify.
- ❤️ Guardar la canción favorita del usuario.
- 🔔 Crear alarmas.
- ⏱️ Crear alarmas relativas, por ejemplo: "en 5 minutos".
- 🛑 Detener alarmas mediante comandos.
- 📝 Crear recordatorios.
- 📋 Consultar recordatorios pendientes.
- 🗑️ Eliminar recordatorios.
- 🧠 Guardar preferencias del usuario.
- 🕐 Informar la hora.
- 📅 Informar la fecha.
- 👋 Reconocer diferentes saludos y despedidas.

---

## 🛠️ Tecnologías utilizadas

El proyecto utiliza principalmente:

- Python
- Tkinter
- SpeechRecognition
- PyAudio
- pyttsx3
- Spotipy
- Spotify Web API
- JSON
- Threading
- Webbrowser

---

## 📂 Estructura del proyecto

```text
Proyecto_EVA/
│
├── main.py
├── interfaz.py
├── spotify_control.py
├── alarmas.py
├── recordatorios.py
├── tiempo_eva.py
│
├── config_ejemplo.py
├── requirements.txt
├── .gitignore
└── README.md
```

### Archivos principales

**main.py**

Es el archivo principal de EVA. Procesa los comandos del usuario y conecta las diferentes funciones del asistente.

**interfaz.py**

Contiene la interfaz gráfica desarrollada con Tkinter.

**spotify_control.py**

Contiene las funciones relacionadas con Spotify, como buscar canciones, reproducir música y controlar la reproducción.

**alarmas.py**

Gestiona la creación, reproducción y detención de alarmas.

**recordatorios.py**

Gestiona los recordatorios y su almacenamiento.

**tiempo_eva.py**

Contiene funciones para interpretar horas, fechas y expresiones como:

```text
en 5 minutos
dentro de una hora
3:30 de la tarde
mañana
```

**config_ejemplo.py**

Archivo de ejemplo para configurar Spotify sin publicar las credenciales personales de cada desarrollador.

---

# ⚙️ Instalación

## 1. Clonar el repositorio

Primero se debe clonar el proyecto desde GitHub.

```bash
git clone URL_DEL_REPOSITORIO
```

Después entra a la carpeta:

```bash
cd EVA-Asistente-Virtual
```

> La URL real del repositorio se colocará aquí cuando el proyecto sea publicado en GitHub.

---

## 2. Tener Python instalado

Se recomienda utilizar **Python 3.13** para ejecutar EVA.

Puedes comprobar tu versión con:

```bash
python --version
```

---

## 3. Crear un entorno virtual

Dentro de la carpeta del proyecto:

```bash
python -m venv .venv
```

---

## 4. Activar el entorno virtual

### Windows PowerShell

```powershell
.venv\Scripts\Activate.ps1
```

Cuando esté activado debería aparecer algo parecido a:

```text
(.venv) PS C:\...\Proyecto_EVA>
```

---

## 5. Instalar las dependencias

Con el entorno virtual activado:

```bash
pip install -r requirements.txt
```

Esto instalará las librerías necesarias para ejecutar EVA.

---

# 🎵 Configuración de Spotify

Para utilizar las funciones de Spotify, cada desarrollador debe utilizar su propia configuración.

El archivo:

```text
config.py
```

no está incluido en el repositorio porque puede contener información privada de configuración.

En el proyecto encontrarás:

```text
config_ejemplo.py
```

Crea una copia y llámala:

```text
config.py
```

Su estructura debe ser:

```python
SPOTIFY_CLIENT_ID = "TU_CLIENT_ID"

SPOTIFY_REDIRECT_URI = (
    "http://127.0.0.1:8888/callback"
)
```

Cada desarrollador debe colocar su propio Client ID de Spotify.

El Redirect URI utilizado por EVA es:

```text
http://127.0.0.1:8888/callback
```

Este mismo Redirect URI debe configurarse en la aplicación correspondiente de Spotify Developer.

> ⚠️ Nunca publiques contraseñas, tokens, archivos de autenticación ni otras credenciales privadas.

---

# 🔐 Archivos privados

El proyecto utiliza un archivo `.gitignore` para evitar publicar archivos privados o innecesarios.

Entre ellos se encuentran:

```text
config.py
.cache
.cache-*
.venv/
__pycache__/
preferencias.json
recordatorios.json
```

Estos archivos **no deben agregarse manualmente al repositorio**.

---

# 🧠 Preferencias y recordatorios

EVA utiliza:

```text
preferencias.json
recordatorios.json
```

para almacenar información local.

Estos archivos no se comparten mediante GitHub.

Si no existen, EVA los crea automáticamente al ejecutarse.

De esta manera, cada desarrollador tendrá sus propias preferencias y recordatorios sin compartir información personal con los demás colaboradores.

---

# ▶️ Ejecutar EVA

Después de instalar las dependencias y configurar Spotify, ejecuta:

```bash
python main.py
```

Se abrirá la interfaz de EVA y podrás utilizar comandos mediante texto o voz.

---

# 🎤 Ejemplos de comandos

Algunos ejemplos de comandos que EVA puede reconocer son:

```text
EVA, abre calculadora

EVA, abre Chrome

EVA, abre Spotify

EVA, busca inteligencia artificial en Internet

EVA, reproduce una canción

EVA, pon mi canción favorita

EVA, pausa la música

EVA, siguiente canción

EVA, qué hora es

EVA, qué fecha es hoy

EVA, pon una alarma a las 4 de la tarde

EVA, pon una alarma en 5 minutos

EVA, detener alarma

EVA, recuérdame estudiar en 20 minutos
```

Los comandos disponibles pueden ampliarse conforme avance el desarrollo.

---

# 🤝 Cómo colaborar

Para evitar modificar directamente la versión principal de EVA, se recomienda trabajar utilizando ramas de Git.

## 1. Actualizar el proyecto

Antes de comenzar a trabajar:

```bash
git pull
```

---

## 2. Crear una nueva rama

Por ejemplo, si quieres mejorar la interfaz:

```bash
git checkout -b mejora-interfaz
```

Otros ejemplos:

```bash
git checkout -b mejora-spotify
```

```bash
git checkout -b nuevos-comandos
```

```bash
git checkout -b mejora-recordatorios
```

---

## 3. Realizar los cambios

Modifica los archivos necesarios y prueba que EVA siga funcionando correctamente.

Después puedes comprobar los cambios con:

```bash
git status
```

---

## 4. Preparar los cambios

```bash
git add .
```

---

## 5. Crear un commit

Ejemplo:

```bash
git commit -m "Mejorar interfaz de EVA"
```

El mensaje debe explicar brevemente qué se modificó.

---

## 6. Subir la rama

```bash
git push origin nombre-de-la-rama
```

Por ejemplo:

```bash
git push origin mejora-interfaz
```

---

## 7. Crear un Pull Request

Después de subir la rama, se puede crear un **Pull Request** en GitHub.

Esto permite:

- Revisar el código.
- Comentar cambios.
- Detectar posibles errores.
- Proponer mejoras.
- Aprobar los cambios antes de incorporarlos a la versión principal.

---

# ⚠️ Recomendaciones para colaboradores

Antes de enviar cambios:

- Comprobar que EVA inicia correctamente.
- Probar las funciones modificadas.
- No publicar credenciales.
- No publicar archivos `.cache`.
- No subir el entorno `.venv`.
- No modificar `.gitignore` sin necesidad.
- Utilizar mensajes de commit descriptivos.
- Trabajar en una rama diferente para cada mejora.

---

# 🔮 Próximas mejoras

Algunas funciones que se pueden desarrollar en futuras versiones:

- 🎨 Mejorar la interfaz gráfica.
- 🎤 Mejorar el reconocimiento de comandos naturales.
- 📝 Mejorar el sistema de recordatorios.
- 🔔 Mejorar las alarmas.
- 🎵 Añadir nuevas funciones de Spotify.
- 🧠 Mejorar el aprendizaje de preferencias.
- 🌐 Ampliar las funciones relacionadas con Internet.
- ⚙️ Mejorar el manejo de errores.
- 📦 Facilitar la instalación del proyecto.
- 🔌 Crear nuevas integraciones.
- 🧩 Organizar EVA utilizando una arquitectura más modular.

---

# 🧑‍💻 Desarrollo

EVA se encuentra actualmente en desarrollo.

Las funciones pueden cambiar, mejorarse o ampliarse conforme avance el proyecto.

Las contribuciones mediante ramas y Pull Requests son bienvenidas.

---

# 📄 Proyecto académico

EVA fue desarrollado con fines educativos como un proyecto de **Fundamentos de Programación**.

El objetivo es aplicar conceptos de programación mediante la construcción progresiva de un asistente virtual personalizado.

---

## 🤖 EVA

**Asistente Virtual Personalizado desarrollado en Python.**