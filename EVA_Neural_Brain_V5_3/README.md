# EVA Neural Brain V5.3 — lluvia Matrix

Demostración independiente para Windows, Python 3.13 y PySide6. Conserva el
cerebro holográfico, esfera, estrellas, circuitos, estados y voz **simulada** de
V5.2. No importa el backend de EVA ni utiliza micrófono, TTS o audio real.

## Ejecutar

Desde `Proyecto_EVA`, con el entorno existente:

```powershell
.\.venv-prototipos\Scripts\python.exe .\EVA_Neural_Brain_V5_3\run_demo.py --auto
```

También puede abrirse `iniciar_windows.bat`. Sin opciones comienza en calidad
alta. Opciones combinables:

```powershell
.\.venv-prototipos\Scripts\python.exe .\EVA_Neural_Brain_V5_3\run_demo.py --low --state HABLANDO
.\.venv-prototipos\Scripts\python.exe .\EVA_Neural_Brain_V5_3\run_demo.py --gentle --panel
```

`--no-voice` desactiva la reacción sintética; `--voice-intensity 0.65` ajusta su
intensidad. Los controles permiten elegir los siete estados, calidad, movimiento
suave, pausa y paneles de demostración. Minimizar suspende la animación. La rueda
cambia el acercamiento y el doble clic restaura la vista.

## Copia independiente

Copiar esta carpeta completa, incluyendo `assets/`, `qml/` y los shaders `.qsb`.
No necesita otras versiones de EVA. `previews/` contiene evidencia y puede
omitirse al distribuir. Requiere un intérprete Python 3.13 con PySide6; se probó
con 6.12.0. En un equipo nuevo, si no existe un entorno adecuado:

```powershell
cd C:\ruta\EVA_Neural_Brain_V5_3
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe run_demo.py --auto
```

No se instalaron dependencias durante este desarrollo. Conservar la atribución
y licencia del modelo en [assets/ATTRIBUTION.md](assets/ATTRIBUTION.md).

## Fondo Matrix

- Un único `ShaderEffect` cubre toda la ventana. Cada columna tiene velocidad,
  fase, tamaño, brillo y longitud deterministas; no se regeneran posiciones.
- Cabezas verde pálido, colas de 15–39 celdas con degradado y renovación suave
  de ceros y unos. Un atlas SVG propio evita cientos de objetos de texto QML.
- Separación de columnas de 18 píxeles lógicos en alta y 28 en reducida.
  Variaciones de tamaño y opacidad sugieren profundidad. No usa un blur costoso.
- Predomina verde con una contribución pequeña del color del estado. En STANDBY
  se atenúa y ralentiza; movimiento suave reduce la velocidad general.
- La exclusión calcula la proyección de la esfera según cámara y viewport:
  interior totalmente transparente, margen de 14 píxeles y transición exterior
  del 20 % del radio. Sigue zoom, redimensionamiento y apertura del panel.
- Los controles, encabezado y panel tienen atenuación adicional. El cerebro y
  las estrellas conservan sus materiales y animaciones.
- Usa el reloj de escena existente, sin temporizadores adicionales. Pausa y
  minimización detienen también la lluvia.

La sensación de rodear la esfera procede de la máscara suave; las trayectorias
siguen siendo verticales, sin una simulación de fluidos.

## Archivos y compilación del shader

El cambio visual está en `qml/BinaryField.qml`, `qml/Main.qml`,
`qml/shaders/matrix.frag`, su compilado `matrix.frag.qsb` y
`assets/binary_glyphs.svg`. El resto del renderizado proviene de V5.2.
`geometry.py`, `performance.py` y `voice_reactivity.py` registran ahora
`EVABrainV53`; `run_demo.py` y `requirements.txt` identifican esta versión.

El `.qsb` incluido permite ejecutar sin compilar. Solo al editar el shader,
desde la raíz del proyecto y usando la herramienta ya disponible en PySide6:

```powershell
.\.venv-prototipos\Scripts\pyside6-qsb.exe --glsl '100es,120,150' --hlsl 50 --msl 12 -o EVA_Neural_Brain_V5_3/qml/shaders/matrix.frag.qsb EVA_Neural_Brain_V5_3/qml/shaders/matrix.frag
```

Se sigue la interfaz de uniformes y texturas de
[Qt ShaderEffect](https://doc.qt.io/qt-6/qml-qtquick-shadereffect.html).

## Validación

Consultar [VALIDACION.md](VALIDACION.md) para mediciones, comparación con V5.2,
capturas y límites. Ejecutar las pruebas gráficas una por una:

```powershell
.\.venv-prototipos\Scripts\python.exe -B .\EVA_Neural_Brain_V5_3\tools\verify_matrix.py
.\.venv-prototipos\Scripts\python.exe -B .\EVA_Neural_Brain_V5_3\tools\verify_interface.py
.\.venv-prototipos\Scripts\python.exe -B .\EVA_Neural_Brain_V5_3\tools\verify_voice.py
.\.venv-prototipos\Scripts\python.exe -B .\EVA_Neural_Brain_V5_3\tools\verify_policy.py
.\.venv-prototipos\Scripts\python.exe -B .\EVA_Neural_Brain_V5_3\tools\verify_portable.py
.\.venv-prototipos\Scripts\python.exe -B .\EVA_Neural_Brain_V5_3\tools\benchmark_matrix.py --seconds 30
```

El benchmark admite `--before` para leer V5.2 si está al lado; esa opción de
comparación no es necesaria para ejecutar ni validar la copia independiente.
