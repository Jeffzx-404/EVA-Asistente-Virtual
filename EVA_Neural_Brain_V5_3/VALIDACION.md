# Validación de EVA Neural Brain V5.3

Fecha: 20 de noviembre de 2026. Windows, Python 3.13.15, PySide6 6.12.0.
Se ejecutaron ventanas Qt nativas y se inspeccionaron sus capturas reales.
No se trata de un render simulado ni de pruebas exclusivamente sin pantalla.

## Comparación visual

Se comparó `V5.2/previews/state-LISTA.png` con
[V5.3 en LISTA](previews/state-LISTA.png): V5.2 presenta grupos pequeños de
binario azul en ambos extremos. V5.3 presenta columnas verdes individuales,
cabezas más claras y estelas largas por los laterales y zonas superior e
inferior. La esfera conserva un área despejada y el cerebro sigue destacando
por su luminosidad. Los circuitos y estrellas continúan visibles.

Se inspeccionaron también [calidad reducida](previews/low-full.png) y
[ventana compacta con panel](previews/compact-panel.png). En reducida disminuye
la densidad sin eliminar cabezas ni colas. El panel compacto conserva el
comportamiento superpuesto heredado: al abrirlo tapa parte del cerebro; puede
cerrarse para recuperar la composición completa.

La referencia externa descrita por el usuario no estuvo disponible como imagen
accesible en esta ejecución; la comparación directa fue con las capturas de
V5.2. La evaluación temporal se apoya en capturas separadas y medición de frames,
no en una sesión prolongada de observación manual.

## Pruebas realizadas

| Prueba | Resultado y evidencia |
|---|---|
| Recursos GLB, índices, geometría y sintaxis Python | PASS en `verify_matrix.py`; recursos locales válidos |
| LISTA, ESCUCHANDO, PROCESANDO, HABLANDO, ACLARACIÓN, ERROR y STANDBY | PASS; colores enlazados y geometría estable |
| Máscara GPU | PASS; suma alfa **0** en 38.668 muestras interiores; control sin máscara vuelve a mostrar lluvia en el centro |
| Cobertura de cuatro regiones | PASS; presencia de binario a izquierda, derecha, arriba y abajo en alta y reducida |
| Movimiento de lluvia | PASS; 14.334 píxeles cambian en 200 ms en la imagen de prueba reducida a 640 píxeles de ancho |
| Reducción de densidad | 10.871 muestras visibles en alta frente a 7.320 en reducida, con igual tiempo y máscara |
| Zoom y redimensionamiento | PASS; cámara 560/800, ventanas 860×640, 1280×760 y 1400×820, panel y maximizar/restaurar |
| Interfaz y estados rápidos | PASS; botones, teclado, paneles, entrada y micrófono demostrativos; ERROR cancelado correctamente |
| Calidad automática | PASS; integración QML y política con muestras sintéticas explícitas; histéresis y recuperación |
| Movimiento suave, pausa y minimización | PASS; avance reducido o reloj congelado según modo; monitor suspendido |
| Voz sintética | PASS; pausas, ataque/decaimiento, independencia de FPS, suspensión, límites e invocación encolada |
| Cierre | PASS; temporizadores detenidos, voz suspendida y procesos con salida 0 |
| Copia independiente | PASS; arranque público en HABLANDO/reducida y prueba Matrix completa fuera del proyecto, sin caché QML ni rutas heredadas |
| Advertencias Qt | Ninguna en las ejecuciones verificadas |

Informes completos: [Matrix](previews/matrix-validation.json),
[interfaz](previews/interface-validation.json),
[voz](previews/voice/signal-validation.json) y
[portabilidad](previews/portability.json). La prueba de portabilidad copió los
43 archivos de código/recursos existentes entonces; después solo se añadieron
estos documentos y la nota de atribución. No depende de un shader en caché.

## Rendimiento observado

Benchmark guardado durante la implementación: HABLANDO, modo cine, 1280×760
píxeles lógicos, escala DPI 1,25. Dos segundos de calentamiento por perfil;
30 segundos medidos por perfil en V5.3, 20 en V5.2. Una ventana a la vez, sin
capturador concurrente. FPS calculados desde `frameSwapped`.

| Calidad | V5.2 FPS | V5.3 FPS | V5.3 p95 entre frames | CPU V5.3* | Memoria V5.3** |
|---|---:|---:|---:|---:|---:|
| Alta | 57,95 | 59,84 | 18,32 ms | 49,90 % | 308,2 MiB |
| Reducida | 59,99 | 59,85 | 18,23 ms | 24,32 % | 138,2 MiB |
| Automática | 58,64 | 59,40 | 18,45 ms | 41,51 % | 132,1 MiB |

\* Tiempo de CPU del proceso respecto a un núcleo, no porcentaje total del equipo.
\** Working set al final del perfil, no VRAM. Windows puede recortar el working
set; no usar diferencias entre ejecuciones para concluir una fuga o un ahorro
garantizado. Automática terminó en alta. La medición observada no muestra una
degradación significativa de FPS, pero tampoco demuestra una mejora universal.

Los FPS superpuestos en capturas funcionales pueden ser menores porque esas
pruebas leen geometría, capturan imágenes y cambian estados; no son el benchmark.
Datos: [antes](previews/benchmark-before.json) y
[después](previews/benchmark-after.json).

## Conservación y límites

- V5.2 conserva sus **95 archivos**, todos con SHA-256 idéntico al manifiesto
  anterior al trabajo (`previews/v52-baseline.json`).
- Solo se añadieron o modificaron archivos dentro de V5.3. Backend y versiones
  anteriores intactos. Sin instalaciones ni conexión a voz/audio reales.
- Git se consultó en modo lectura; sin `add`, `commit`, `push`, `merge` ni cambio
  de rama. Se mantuvo la rama encontrada: `interfaz-neural-orb`.
- Profundidad aparente por tamaño, velocidad y opacidad; sin desenfoque gaussiano
  ni simulación física del flujo alrededor de la esfera.
- Pruebas limitadas a este equipo Windows y DPI 1,25; no se validaron todas las
  GPU, múltiples monitores, ejecución de varias horas ni empaquetado en EXE.
- Las pruebas automáticas de calidad provocan cambios con muestras sintéticas;
  el benchmark real no necesitó reducir automáticamente la calidad.
