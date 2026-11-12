# Recordatorios: separar el aviso del almacén

Base de esta etapa: `53d1994`, rama `inteligencia-local-eva`.

Actualización posterior: la investigación y el tratamiento limitado del error
Windows se documentan en [PERSISTENCIA_WINERROR5.md](PERSISTENCIA_WINERROR5.md).
Su regresión posterior aprobó 471 pruebas y omitió una por reentrenamiento.
Los resultados de abajo conservan la evidencia histórica de esta etapa.

## Causa y reproducción

`revisar_recordatorios` mantenía abierta `_almacen.transaccion()` mientras
`main.avisar_recordatorio` hablaba y esperaba `interfaz.mostrar_recordatorio`.
La transacción mantenía el `RLock` global de persistencia y el bloqueo del
archivo `recordatorios.json.lock`. El primero también detenía las escrituras
de preferencias en otros hilos. El diálogo sólo devolvía `True` después de
cerrarse correctamente con `ok`; encolar el aviso nunca equivalía a entregarlo.

La prueba `test_aviso_pendiente_permite_crear_sin_esperar_confirmacion` falló
antes de la corrección: otra creación no terminaba mientras el aviso simulado
seguía abierto. Su evidencia local está en
`tests/resultado_aviso_bloqueo_antes.txt`.

## Corrección y orden de bloqueos

1. Un bloqueo de hilo no bloqueante y un bloqueo de archivo independiente,
   `recordatorios.json.avisos.lock`, permiten sólo un notificador por almacén
   entre procesos de esta versión. Un segundo vigilante no espera: vuelve a su
   ciclo habitual sin entregar el mismo lote.
2. Una transacción corta lee y valida los datos, identifica los vencidos y
   asigna identificadores a los que todavía no los tienen. Si falla esa
   escritura, no comienza la entrega.
3. Antes de cada aviso se comprueba brevemente que sigue existiendo la misma
   entrada. Voz y diálogo se ejecutan fuera de cualquier transacción de datos.
   El guardia de avisos permanece adquirido; los escritores no lo utilizan.
4. Sólo un resultado exactamente `True` autoriza la retirada. Otra transacción
   relee el archivo y elimina exclusivamente la entrada con la misma identidad
   y contenido. Conserva las creaciones y modificaciones concurrentes.
5. Los errores liberan el guardia mediante `finally`. Se conservan la escritura
   atómica, las copias de recuperación y las pausas de reintento existentes.

Nunca se adquiere el guardia de avisos desde una transacción de datos. No se
espera a otro notificador manteniendo el almacén. El callback puede acceder a
persistencia sin el bloqueo circular que existía antes.

## Formato e identidad

El JSON sigue siendo una lista de los mismos objetos. Se añade el campo
opcional `id_aviso` a los recordatorios vencidos antes de su primera entrega.
Los archivos antiguos sin ese campo siguen siendo válidos. Los futuros no
se modifican. Los identificadores presentes deben ser cadenas no vacías,
de hasta 128 caracteres y no repetidas; un archivo inválido conserva el
mecanismo de recuperación existente.

Este pequeño cambio es necesario para diferenciar dos entradas idénticas y
evitar el caso de borrar un recordatorio, recrearlo durante el aviso y recibir
después la confirmación del antiguo. `id_aviso` **no significa entregado** ni
«en curso». No cambia `completado`; los completados heredados vencidos se
siguen retirando sin aviso. No hay un estado persistente de reserva que pueda
quedar abandonado al cerrar EVA.

Los lectores antiguos de EVA toleraban campos adicionales. No obstante, no se
garantiza exclusión de avisos con una versión antigua ejecutándose al mismo
tiempo, porque aquella no conoce el nuevo guardia de entrega.

## Tkinter, confirmaciones y cierre

`main.py` y la voz no cambian. El trabajador sigue esperando el resultado de
un diálogo en el hilo principal de Tkinter. Se mantienen la cola y el mecanismo
de cierre existentes; ninguna escritura se traslada al hilo Tk.

Si la cola no llega a mostrar el aviso en 30 segundos, la solicitud falla y
queda invalidada: un callback despachado después no abre un diálogo obsoleto.
El recordatorio se conserva para reintento. Un diálogo ya visible conserva la
espera humana hasta `ok` o el cierre de EVA; no se autoacepta ni se abre un
segundo aviso al cumplirse ese plazo. Esa espera voluntaria no retiene el
almacén, aunque mantiene en orden los avisos pendientes.

Al cerrar la interfaz, su evento despierta al trabajador sin confirmar. Si el
cierre de recordatorios se detecta tras el callback, tampoco se retira la
entrada. El SO libera el guardia cuando termina el proceso; el archivo de
bloqueo vacío se conserva para que todas las instancias usen el mismo archivo.

## Reinicios y límites reales

- Un recordatorio confirmado y retirado correctamente no reaparece.
- Un error de interfaz o guardado conserva la entrada; se vuelve a intentar.
- Un cierre inesperado después de mostrar/confirmar pero antes de persistir la
  retirada puede repetir el aviso al reiniciar. Se prefiere repetición a pérdida:
  **no se garantiza entrega exactamente una vez**.
- Cancelar o modificar una entrada evita que la confirmación antigua borre
  otra; no puede retirar una frase de voz o un diálogo que ya comenzó.
- Un callback externo que no coopere puede retener al notificador; no retiene
  el almacén. No se intenta terminar hilos por la fuerza ni cancelar una llamada
  de voz nativa en curso. La espera del diálogo visible es deliberada.

## Archivos y verificaciones

Código modificado: `recordatorios.py`, `persistencia.py`, `interfaz.py`.
Pruebas y evidencias locales en `tests/`, ignorado por Git. No cambian el
enrutador, alarmas, Whisper, modelos, Spotify, Gemini ni las opciones por defecto.

Las pruebas usan almacenamiento temporal, avisos y sonido simulados; incluyen
hilos y procesos reales para verificar exclusión y recuperación al terminar un
proceso de prueba. Las pruebas Tkinter usan diálogos simulados.

Resultados:

- 14 pruebas nuevas en `test_aviso_sin_bloqueo.py`, incluidas en un bloque de
  69 pruebas de auditoría, notificación, cierre e integración: todas aprobadas
  (11,412 segundos). Evidencia: `tests/resultado_aviso_bloqueo_ciclo.txt`.
- Última regresión completa: **458 aprobadas, una fallida y una omitida**
  (460 descubiertas; 145,311 segundos). La omitida exige reentrenamiento.
  Evidencia: `tests/resultado_aviso_bloqueo_final.txt`. No se entrenaron modelos.
- El fallo restante es `test_80_creaciones_concurrentes_sin_perdidas`:
  Windows devuelve intermitentemente `WinError 5` en `os.replace`. No es una
  espera del guardia de entrega; ese ensayo sólo crea recordatorios.
- Se reprodujo también cargando `persistencia.py` y `recordatorios.py` del
  commit publicado `53d1994` en una copia temporal: 7 de 30 ensayos de 80
  creaciones fallaron por el mismo acceso denegado. Los 10 ensayos iniciales
  de esa base habían pasado. Evidencias: archivos
  `tests/resultado_aviso_concurrencia_base_publicada.txt` y
  `tests/resultado_aviso_concurrencia_base_extendida.txt`.
- En 10 ensayos adicionales del código actual, dos volvieron a encontrar el
  acceso denegado. Se comprobó antes de exigir éxito total que el JSON contenía
  exactamente las creaciones confirmadas, sin pérdidas ni duplicados de éstas.
  Esa comprobación pasó en los 10 ensayos. Evidencia:
  `tests/resultado_aviso_concurrencia_integridad.txt`.

Por tanto, **la regresión global no queda completamente aprobada**. Se conoce
la operación y el error concreto, pero no se identificó qué condición de Windows
deniega esas sustituciones. No se atribuye a antivirus, permisos u otro proceso
sin evidencia. No se añadieron reintentos silenciosos ni se alteró la política
de escritura atómica para conseguir un resultado verde. Este problema previo
queda pendiente de investigación antes de publicar.

Las pruebas históricas se adaptaron para admitir el identificador opcional,
interrumpir el guardado de confirmación (en lugar de la nueva identificación),
aislar el evento de cierre de cada sesión y exigir que las preferencias ya no
esperen al diálogo. Las huellas antiguas exceptúan los tres archivos autorizados
y el índice de commits anteriores; una nueva prueba compara los demás módulos
y modelos con `53d1994` y comprueba que no haya cambios preparados en Git.

## Validación manual pendiente

Con recordatorios sintéticos: dejar un aviso abierto y crear otro recordatorio
desde una segunda instancia, o dejar que termine una operación ya iniciada.
Comprobar también una escritura de preferencias. El diálogo nativo sigue siendo
modal: no se habilitan los controles de su ventana propietaria mientras está
abierto, aunque Tk sigue procesando eventos. Confirmar y comprobar que sólo
desaparece el atendido. Probar cierre con un aviso abierto,
reinicio con pendientes y dos instancias de la misma versión. Verificar voz y
diálogo reales; las simulaciones no certifican micrófono, altavoces ni el
comportamiento del diálogo nativo de Windows.
Además, investigar el acceso denegado intermitente al reemplazar JSON en este
equipo; no dar por resuelta esa condición sólo porque un ensayo aislado pase.
