# EVA Hologram Face V1

Demo independiente en PySide6/QML. Continúa el trabajo existente y toma como
referencia principal la imagen del usuario «Imagen de ChatGPT 23 nov 2026,
08_04_00 p.m.png». No importa ni modifica el backend de EVA, Tkinter o Neural
Brain V5.3. La interfaz tiene controles reales; no muestra una captura completa
como sustituto de la aplicación.

## Corrección actual: recuperar tamaños compactos — 27 de noviembre de 2026

Se conservaron los ajustes guardados antes de la interrupción. La composición
recupera las proporciones anteriores al rediseño responsivo: lateral 217×676,
conversación 520×659, rostro 490×600, métricas 373×557 y entrada 1224×73
unidades de diseño. Los círculos de métricas tienen un máximo de 94 unidades
y las burbujas recuperan sus alturas compactas, conservando el ajuste al texto.
No se cambiaron mensajes, colores, glass, recursos del rostro ni logo.
El menú conserva la mejora de alineación de iconos, textos y selección.

La base de 1672×941 se centra en el área cliente. Su escala es
`min(1, anchoDisponible/1672, altoDisponible/941)`: nunca crece por encima de
su tamaño de diseño, y se reduce proporcionalmente en ventanas pequeñas.
El fondo continúa cubriendo toda la ventana. Al maximizar quedan márgenes
simétricos cuando sobra espacio; las tarjetas no se estiran para llenarlo.
No existe scroll global; únicamente se desplaza el historial de conversación.

Archivos de esta corrección (incluido el trabajo conservado de la sesión anterior):
`qml/Main.qml`, `qml/components/MessageBubble.qml`,
`qml/components/MetricsPanel.qml`, `tools/verify_ui.py` y `README.md`.
Las capturas e informes están en `previews/compact-*` y
`previews/validation-compact-*.json`. Esta continuación completó la prueba
pendiente y la documentación; no fue necesario volver a modificar los QML.

### Validación de la composición compacta

- **PASS, Windows al 125 %:** prueba funcional completa realizada el 26 de
  noviembre sobre estos mismos QML: navegación, envío/Enter, conversación,
  exportación local, movimiento reducido, redimensionamiento, minimización,
  restauración y cierre. Sin errores ni advertencias Qt.
- **PASS, DPI efectivo 100 %:** prueba pendiente completada el 27 de noviembre,
  con ventana normal, maximizada, pantalla completa y áreas de 900×600,
  1366×768, 1536×864, 1920×1080 y 2560×1440. Comprobados centrado, límites,
  alineación del menú, tamaño máximo y navegación mínima. Sin mensajes Qt.
- Se inspeccionaron las capturas de 1366×768, Full HD y maximizada y se
  compararon con el diseño ampliado y las capturas glass anteriores.
- Los hashes del rostro, `HologramStage.qml`, `EvaMark.qml` y `main.py`
  coinciden con los previos. No se modificó el backend, Neural Brain V5.3,
  otras versiones ni la rama. No se realizaron operaciones Git de escritura.

Capturas para comparar (se conservan también todas las anteriores):

| Caso | Antes de corregir | Resultado compacto |
| --- | --- | --- |
| 1366×768, DPI 100 % | [Rediseño responsivo](previews/responsive-100-1366x768.png) | [Actual](previews/compact-100-1366x768.png) |
| Full HD, DPI 100 % | [Rediseño responsivo](previews/responsive-100-1920x1080.png) | [Actual, pantalla completa nativa](previews/compact-100-fullscreen.png) |
| Maximizada, Windows 125 % | [Glass anterior al rediseño](previews/glass-final.png) | [Actual](previews/compact-125-final.png) |
| Ventana normal, Windows 125 % | [Glass anterior al rediseño](previews/glass-normal.png) | [Actual](previews/compact-125-normal.png) |

Informes: [funcional 125 %](previews/validation-compact-125.json) y
[matriz 100 %](previews/validation-compact-100.json).

Limitaciones: al mínimo 900×600 los textos se reducen junto con la composición;
se prioriza conservar las proporciones solicitadas. El mínimo se expresa en
píxeles lógicos. El monitor físico es Full HD con Windows al 125 %; se obtuvo
100 % efectivo mediante `QT_SCALE_FACTOR=0.8` solo en el proceso de prueba.
Las áreas mayores que la pantalla se capturaron ampliando la escena Qt
(`expanded_scene` en los informes), no usando un monitor físico QHD. La captura
`compact-100-fullscreen.png` sí corresponde a pantalla completa nativa de
1920×1080. No se repitió una medición de FPS en esta corrección de layout.

Ejecutar desde la raíz del proyecto:

```powershell
.\.venv-prototipos\Scripts\python.exe -B .\EVA_Hologram_Face_V1\run_demo.py
```

Las secciones siguientes son el historial de revisiones; sus descripciones de
layout no sustituyen la composición compacta descrita arriba.

## Historial: menú y distribución responsiva — 26 de noviembre de 2026

Esta revisión sustituye el escalado global de la composición por anchors y
dimensiones independientes. La escena principal permanece a escala 1: las
columnas usan anchos proporcionales con límites, márgenes de 12–32 unidades y
separaciones de 10–24. La conversación y las tarjetas aprovechan el alto útil,
y la barra inferior se ancla entre la conversación y el micrófono.

Por debajo de 1240 unidades de ancho o de 690 de alto, Sistema/Red/Procesos se
redistribuyen en una fila inferior. Todos siguen visibles sin scroll global.
EVA permanece centrada en su columna: solo su ilustración, órbitas y pedestal
se ajustan proporcionalmente como una unidad, sin deformación ni cambios en
sus recursos. El logo conserva sus trazos y proporciones. Las fuentes ya no se
reducen con toda la ventana; el menú usa 15/18 px lógicos y el texto de mensajes
16/17 según el ancho. En el mínimo, el rostro ocupa menos alto para mantener
las métricas y los controles visibles; el historial sí se desplaza internamente.

El menú conserva filas de 55 unidades y separación de 13. Se eliminó el padding
implícito del botón y se centró un grupo común de icono/texto; los iconos y los
textos comparten columnas. La selección usa exactamente el rectángulo de su
botón. Las burbujas y el recordatorio ajustan altura según las líneas de texto;
no se cambió ningún mensaje ni dato de ejemplo. Los detalles de las secciones
usan espaciado compacto cuando el alto disponible lo requiere, sin añadir scroll.

Archivos modificados: `qml/Main.qml`, `qml/components/ConversationPanel.qml`,
`MessageBubble.qml`, `MetricsPanel.qml`, `MetricRing.qml`, `StatusPill.qml`,
`tools/verify_ui.py` y `README.md`. Evidencia nueva en `previews/responsive-*`.
No se modificaron `GlassPanel.qml`, la paleta, los efectos, `EvaMark.qml`,
`HologramStage.qml`, la textura del rostro, `main.py` ni otros módulos de EVA.
Los hashes de los recursos protegidos y de `main.py` se comprobaron antes/después.

### Tamaños y DPI comprobados

La matriz prueba áreas lógicas de 900×600, 1366×768, 1536×864, 1920×1080 y
2560×1440, además de ventanas nativas normal, maximizada y pantalla completa.
Se comprueban límites de los paneles, ausencia de solapamientos, posición del
rostro, centrado y columnas del menú, etiquetas completas y círculos dentro de
Sistema. A 100 % esas cinco áreas generan capturas con las dimensiones físicas
exactas indicadas.

El equipo tiene un monitor Full HD con Windows al 125 %. Los factores efectivos
100 % y 150 % se prueban mediante `QT_SCALE_FACTOR=0.8` y `1.2` exclusivamente en
los procesos de prueba; no se cambió el escalado de Windows. Cuando un área no
cabe en el monitor, se amplía el contenido Qt y se captura mediante
`grabToImage`: es renderizado nativo de Qt en Windows, pero **no una prueba en
un monitor físico QHD**. Cada informe distingue `logical`, `content_logical`,
`pixels`, `device_pixel_ratio` y `expanded_scene`.

El mínimo de la aplicación sigue siendo 900×600 **lógico**: equivale a
1125×750 físicos al 125 % y 1350×900 al 150 %, más los bordes de Windows.
No se promete que ese mínimo quepa en una pantalla física de 900×600 con DPI alto.

La suite funcional completa a 125 % valida navegación, envío, exportación UTF-8,
desplazamiento de conversación, movimiento reducido, redimensionamiento,
minimización/restauración y cierre. También comprueba que Configuración y las
otras secciones quepan sin scroll al mínimo. Las variantes 100/150 % ejecutan
la matriz de tamaños y navegación mínima. Los resultados finales y los mensajes
Qt quedan en los informes siguientes.
Las tres ejecuciones finales resultaron **PASS**, sin errores ni advertencias Qt.

- [Normal al 125 %](previews/responsive-125-normal.png)
- [Maximizada al 125 %](previews/responsive-125-final.png)
- [Mínimo 900×600](previews/responsive-100-900x600.png)
- [1920×1080](previews/responsive-100-1920x1080.png)
- [2560×1440, escena ampliada](previews/responsive-100-2560x1440.png)
- [Maximizada al 150 % efectivo](previews/responsive-150-final.png)
- Informes: [100 %](previews/validation-responsive-100.json),
  [125 %](previews/validation-responsive-125.json),
  [150 %](previews/validation-responsive-150.json).

Para repetir la prueba funcional en el DPI de Windows actual:

```powershell
.\.venv-prototipos\Scripts\python.exe -B .\EVA_Hologram_Face_V1\tools\verify_ui.py
```

Esta distribución ampliada fue reemplazada por la corrección compacta descrita
al inicio. Sus capturas se conservan únicamente para comparación.

## Ajuste anterior: glass y encabezado — 26 de noviembre de 2026

Sobre el pulido aprobado se refinaron únicamente las superficies y sus acentos:
fondos translúcidos azul noche, borde luminoso fino, reflejo superior tenue y
tres capas de sombra de baja opacidad. No se añadió blur de fondo. Las tarjetas
comparten radios de 24 unidades; entrada y estado conservan su forma de cápsula.
Los azules/cian y violetas de selección, indicadores y controles son algo más
nítidos, sin alterar el fondo ni la ilustración central.

Se eliminó por completo «Buscar en EVA…», sin reemplazo. También se retiraron
Ctrl+K y el icono de búsqueda del encabezado de conversación que abrían ese
campo. Exportación, avisos y mensajes de ejemplo se conservan. El conjunto
«EVA | Asistente Inteligente» pasó de x155 a x26, alineado al panel izquierdo;
el logo mantiene tamaño, trazos y tipografía. Los iconos superiores derechos
permanecen alineados con las tarjetas derechas. No se añadieron paneles.

Archivos modificados en este ajuste: `qml/Main.qml`,
`qml/components/GlassPanel.qml`, `StatusPill.qml`, `ConversationPanel.qml`,
`MetricsPanel.qml`, `IconButton.qml`, `tools/verify_ui.py` y `README.md`.
Las capturas y los informes nuevos se guardaron en `previews/` con prefijo
`glass-`, `validation-glass` o `performance-glass`; las evidencias anteriores
se conservan.

Validación nativa Windows: **PASS**, sin errores ni advertencias Qt. Se revisaron
normal, maximizada, Full HD, 1366×768 y mínimo 900×600 lógico. Se verificaron
centrado, límites de paneles, ausencia de scroll global, navegación, envío,
exportación UTF-8, estados visuales, movimiento reducido, minimizar/restaurar
y cierre. La geometría del rostro sigue siendo x790, y54, 490×600; los hashes
del retrato, `HologramStage.qml`, `EvaMark.qml` y `main.py` no cambiaron.

El ensayo de ocho segundos de renderizado forzado dio **59,87 FPS**, mediana
16,58 ms y p95 19,27 ms, frente a los 59,86 FPS anteriores. CPU equivalente a
un núcleo: 57,45 % durante ese ensayo y 0,00 % en la muestra de reposo. La CPU
activa fue mayor que el 45,14 % de la muestra previa; estas mediciones breves
no aíslan variaciones de carga ni equivalen al consumo de una pantalla estática.
No hubo caída apreciable de FPS. La translucidez y las sombras se resuelven
mediante geometría sencilla; no se incorporaron dependencias ni shaders.

Evidencia actual: [final maximizada](previews/glass-final.png),
[normal](previews/glass-normal.png), [Full HD](previews/glass-full-hd.png),
[mínimo](previews/glass-minimum.png),
[pruebas](previews/validation-glass.json),
[rendimiento](previews/performance-glass-final.json).
La documentación de las fases anteriores que sigue a continuación conserva
sus resultados históricos; sus referencias a búsqueda ya no describen la UI actual.

## Ejecutar en Windows

Desde `Proyecto_EVA`, usando el entorno ya existente:

```powershell
.\.venv-prototipos\Scripts\python.exe .\EVA_Hologram_Face_V1\run_demo.py
```

También puede abrirse `iniciar_windows.bat`. Requiere Python 3.13 y PySide6
(probado con 6.12.0). No se instalaron dependencias en esta tarea. Para trasladar
la demo, copiar toda esta carpeta y usar un Python con las dependencias de
`requirements.txt`; `previews/` es evidencia opcional y no se necesita al arrancar.

Captura reproducible y tamaño compacto:

```powershell
.\.venv-prototipos\Scripts\python.exe .\EVA_Hologram_Face_V1\run_demo.py --capture .\EVA_Hologram_Face_V1\previews\manual.png
.\.venv-prototipos\Scripts\python.exe .\EVA_Hologram_Face_V1\run_demo.py --width 1000 --height 700
.\.venv-prototipos\Scripts\python.exe .\EVA_Hologram_Face_V1\run_demo.py --maximized
.\.venv-prototipos\Scripts\python.exe .\EVA_Hologram_Face_V1\run_demo.py --reduced-motion
```

## Composición y fidelidad

La referencia de 1672×941 píxeles se trasladó a coordenadas lógicas para
conservar sus proporciones en ventanas amplias:

| Zona | Posición y dimensiones de referencia |
|---|---|
| Navegación | x26, y111, 217×676 |
| Conversación | x260, y111, 520×659 |
| Rostro y órbitas | Centro próximo a x1035, desde y54 |
| Sistema / red / procesos | x1274, ancho373, y111 / 331 / 518 |
| Estado del rostro | x872, y672, 326×74 |
| Entrada | x260, y804, 1224×73 |

Se reprodujeron la paleta azul nocturna/cian/violeta, los paneles redondeados,
el logo orbital y las letras EVA vectoriales, la conversación inicial, las
tarjetas y los controles. El fondo, iconos, pedestal y gráficos se dibujan con
QML/Canvas; los brillos principales usan efectos Qt. Arial aproxima la
tipografía de la imagen sin descargar fuentes de procedencia desconocida.

La composición actual usa anchors y columnas con anchos adaptables; las métricas
se ubican a la derecha o en una fila inferior según el espacio disponible.
Solo la ilustración central se ajusta proporcionalmente. El fondo llena la ventana.
La pantalla principal es un Item sin Flickable ni barras de desplazamiento.
Solo la conversación conserva su desplazamiento interno para mensajes largos.
Tamaño mínimo: 900×600 píxeles lógicos; los breakpoints mantienen legibles los
textos y visibles los paneles. Se probó escala de pantalla Windows
125 %. El lanzador centra la ventana dentro del área disponible del monitor,
teniendo en cuenta los bordes de Windows; `--maximized` permite abrir maximizada.

Se retiraron los tres puntos decorativos superiores, la insignia «⌘ K» de
búsqueda y la insignia «⇧ ↵» junto al envío. Posteriormente se retiró la barra
de búsqueda completa y su atajo; Enter sigue enviando mensajes.
Se conservan el retrato, la familia tipográfica y la composición aprobada.

## Pulido profesional — cierre del 26 de noviembre de 2026

Se conservó íntegramente el pulido de la sesión anterior. En esta continuación
se revisaron los archivos y se completaron las pruebas, la comprobación de
preservación del rostro, las capturas finales y esta documentación. No fue
necesario volver a modificar QML ni rediseñar la interfaz.

El pulido incorpora bordes redondeados más uniformes, tarjetas translúcidas con
degradados y sombras sencillas sin blur de fondo, títulos y datos secundarios
mejor diferenciados, selección lateral menos brillante y acentos cian/violeta
más contenidos. Se refinaron Sistema, Red, Procesos, mensajes, barra de entrada,
envío, micrófono y estados de foco. Las transiciones de hover y pulsación duran
100–120 ms; no hay animaciones decorativas continuas. Se desactivan con
**Configuración → Reducir movimiento**, `--reduced-motion` o al minimizar.
La preferencia de movimiento es local a la sesión; no se guarda ni se vincula
automáticamente a la configuración de accesibilidad de Windows.

Archivos del pulido, todos dentro de esta carpeta:

- Modificados: `qml/Main.qml`, `qml/components/ConversationPanel.qml`,
  `GlassPanel.qml`, `IconButton.qml`, `MessageBubble.qml`, `MetricRing.qml`,
  `MetricsPanel.qml`, `StatusPill.qml`, `run_demo.py`, `tools/verify_ui.py` y
  `README.md`.
- Creado: `tools/measure_ui.py`, para medir tiempos de fotograma.
- Evidencia nueva/actualizada: capturas e informes en `previews/`.

Los hashes SHA-256 de `face-hologram.png`, `HologramStage.qml`, `EvaMark.qml` y
`Background.qml` coinciden con los guardados antes del pulido. El recorte
central del rostro de 440×570 píxeles coincide exactamente antes/después.
La comprobación inicial incluía el borde de búsqueda en los primeros siete
píxeles verticales: esas diferencias no pertenecían al rostro. Se conservó el
informe inicial y se añadió el [resultado corregido](previews/polish-integrity-final.json).

### Pruebas finales en Windows

`tools/verify_ui.py`: **PASS**, sin mensajes Qt. Se probaron apertura centrada,
maximización, Full HD 1920×1080, área de contenido 1366×768, mínimo 900×600
lógico y tres tamaños intermedios. Se inspeccionaron las capturas: todos los
paneles caben, la escala permanece uniforme y no existe scroll principal.
La prueba de 1366×768 usa una ventana del monitor Full HD con DPI 125 %;
no se cambió la resolución física del monitor. En 900×600 lógico los textos
son más pequeños; no se ocultan paneles para compensarlo.

También aprobaron navegación, envío/Enter, rechazo de mensajes vacíos,
búsqueda/Ctrl+K, scroll interno, cambio de estado visual, movimiento reducido,
escritura UTF-8, minimizar/restaurar y cierre. `tools/verify_portable.py` aprobó
el arranque desde una copia independiente, sin caché QML ni backend, con salida
0 y sin mensajes Qt. La exportación comprueba el escritor; no se automatizó
el diálogo nativo completo de guardado.

### Rendimiento observado

Ventana maximizada, 1536×793 lógico, DPI 125 %, pantalla de 60 Hz. El ensayo
fuerza renderizado durante ocho segundos y varía ligeramente la opacidad del
botón de envío. No representa FPS en reposo ni rendimiento de labios animados.

| Medición | Antes del pulido | Final, 26/11 |
|---|---:|---:|
| FPS medios | 59,86 | 59,86 |
| Mediana de intervalo | 16,70 ms | 16,67 ms |
| Percentil 95 | 18,98 ms | 19,03 ms |
| CPU, equivalente a un núcleo | 45,54 % | 45,14 % |
| CPU en dos segundos de reposo | 0,00 % | 0,00 % |

No se observa una regresión importante en este ensayo corto. Los resultados
pueden variar con la carga del equipo; la muestra no garantiza 60 FPS para
futuras animaciones del rostro. La primera ejecución posterior al pulido dio
60,00 FPS y también se conserva como evidencia.

```powershell
.\.venv-prototipos\Scripts\python.exe -B .\EVA_Hologram_Face_V1\tools\measure_ui.py --label revision
```

Capturas: [antes](previews/polish-before.png),
[después, normal](previews/polish-normal.png),
[final maximizada](previews/polish-final.png),
[Full HD](previews/polish-full-hd.png), [1366×768](previews/polish-1366x768.png),
[mínimo](previews/polish-minimum.png),
[movimiento reducido](previews/polish-reduced-motion.png).
Informes: [funcional](previews/validation-polish.json),
[rendimiento final](previews/performance-final-2026-11-26.json),
[portabilidad](previews/portability.json).

El rostro sigue siendo una ilustración estática, sin aparición animada ni
sincronización de voz. La demo mantiene sus respuestas y métricas simuladas.
No se modificaron `main.py`, backend, Tkinter, Neural Brain V5.3 ni otras
versiones. La rama sigue siendo `interfaz-neural-orb`, sin operaciones Git de
escritura. Queda pendiente únicamente la aprobación visual del usuario.

## Funcional y simulado

**Funcional:** navegación entre las cinco secciones, conversación desplazable,
entrada de texto, envío con botón o Enter, rechazo de mensajes vacíos,
exportación UTF-8 mediante diálogo
de guardado, avisos informativos, adaptación de tamaño y cierre.

**Simulado:** todas las respuestas, el recordatorio de ejemplo, alarmas,
servicios, perfil, notificaciones y valores de CPU/RAM/GPU/red/procesos. Los
mensajes nuevos viven solo en memoria, salvo una exportación solicitada.
El texto «He creado un recordatorio» pertenece a la conversación de referencia:
no crea ni guarda un recordatorio real. «Operativa», «Conectado» y «68 activos»
son rótulos de la maqueta. El clip solo muestra un aviso; no abre archivos.

El micrófono cambia únicamente el rótulo visual HABLANDO/ESCUCHANDO y explica
que está desconectado. No hay captura, TTS, llamadas de red, Whisper ni pyttsx3.

## Rostro y futura animación

`assets/face-hologram.png` es una textura **2D estática** con transparencia,
preparada previamente con image_gen a partir de la referencia. Se conserva el
recurso existente. Prompt y procedencia en [assets/GENERACION.md](assets/GENERACION.md).

`HologramStage.qml` separa retrato, órbitas y pedestal. Expone `appearance`,
`speechLevel`, `lipOpening`, `headYaw`, `paused` y `reducedQuality` como puntos de
extensión. Las entradas de energía/labios aún no deforman el rostro ni controlan
audio. No se ha implementado aparición, movimiento continuo ni sincronización.
La textura y los dibujos quedan almacenados; una futura animación podrá usar
propiedades del scene graph. Alcanzar 60 FPS con labios/rostro animados requerirá
medir esa implementación futura, y posiblemente una malla con deformadores.

## Verificación anterior — 25 de noviembre de 2026

Se ejecutó la demo nativa en Windows y se inspeccionaron capturas reales frente
a la referencia. Durante la revisión se corrigieron:

- Sombras CPU grandes del fondo Canvas que demoraban el primer renderizado.
  Se sustituyeron por degradados y trazos; los brillos del estado usan Qt Effects.
- Tipografía y alturas de mensajes que ocultaban la tarjeta del recordatorio.
- Tamaño del rostro y halo rectangular del pedestal.
- Pérdida del enlace de navegación después de enviar/buscar mensajes.
- Foco de avisos para cerrarlos con Escape y etiquetas en ventanas compactas.

La ejecución medida después del ajuste completó captura y cierre en **7,53 s**,
incluyendo una espera programada de 3 s. No es una medición de FPS: esta fase
deliberadamente no mantiene una animación continua.

La suite actualizada `tools/verify_ui.py` aprobó: carga del retrato, navegación real mediante
clics, envío/Enter, entrada vacía, desplazamiento, Ctrl+K y búsqueda, estado
visual, escritura UTF-8 y rechazo de destinos no locales, acceso a las tres
métricas, minimización/restauración y cierre. **Sin errores
ni advertencias Qt** en el resultado final.

Se inspeccionaron capturas del renderizado nativo de Windows en estos casos:

| Caso | Área lógica | Captura física (DPI 125 %) |
|---|---|---|
| Normal centrada | 1338×753 | 1673×941 |
| Maximizada | 1536×793 | 1920×991 |
| Full HD, pantalla completa para la prueba | 1536×864 | 1920×1080 |
| Mínimo soportado | 900×600 | 1125×750 |

También se verificaron los tamaños 1000×700, 1200×650 y 1500×700. Las
comprobaciones geométricas exigen paneles dentro de la ventana, escala uniforme,
centrado y ausencia de desplazamiento principal. El texto es más pequeño al
mínimo, pero no se recortan paneles ni se deforma el rostro. La prueba Full HD
usa el monitor Full HD disponible; no cambia la resolución de Windows. Durante
el ajuste del ensayo, Windows rechazó una ventana normal con contenido Full HD
más sus bordes; se corrigió el ensayo usando pantalla completa. La ejecución
final quedó sin mensajes Qt. La copia independiente también pasó con caché QML
desactivada y código de salida 0.

```powershell
.\.venv-prototipos\Scripts\python.exe -B .\EVA_Hologram_Face_V1\tools\verify_ui.py
.\.venv-prototipos\Scripts\python.exe -B .\EVA_Hologram_Face_V1\tools\verify_portable.py
```

Evidencia de esa etapa anterior: [captura final maximizada](previews/final-updated.png),
[normal](previews/normal-updated.png), [Full HD](previews/full-hd-updated.png),
[mínimo](previews/minimum-updated.png),
[resultado funcional](previews/validation-responsive.json) y
[copia independiente](previews/portability.json).
Las capturas históricas (`final.png`, `compact.png`, `compact-metrics.png`) se
conservan, pero corresponden a la versión anterior con desplazamiento principal.
La prueba de exportación automatizada comprueba el escritor; la interacción
completa con el diálogo nativo de archivos no se automatizó.

## Límites visuales pendientes de aprobación

El retrato generado interpreta los rasgos de la referencia; no es una extracción
idéntica píxel a píxel ni una malla tridimensional. Las curvas del logo, algunas
formas de iconos, el ajuste de texto y los halos son aproximaciones vectoriales.
Se conservaron distribución y paleta, pero no se afirma igualdad exacta con la
imagen. Los controles de ventana nativos de Windows quedan fuera del área de
contenido capturada; los puntos decorativos del encabezado se eliminaron.

## Archivos

- `run_demo.py`, `iniciar_windows.bat`, `requirements.txt`: arranque independiente.
- `qml/Main.qml`: composición, entrada y navegación.
- `qml/components/`: paneles, conversación, burbujas, logo, iconos, métricas,
  fondo, rostro y estado reutilizables.
- `assets/`: retrato transparente y procedencia/prompt.
- `tools/verify_ui.py`, `tools/verify_portable.py`: comprobaciones reproducibles.
- `previews/`: capturas e informes. Se conservaron las capturas anteriores.

En esta continuación solo se editaron archivos de `EVA_Hologram_Face_V1/`.
Las modificaciones previas de `main.py` y de la integración V5.3 se dejaron
intactas. No se cambió de rama ni se ejecutaron operaciones Git de escritura.
