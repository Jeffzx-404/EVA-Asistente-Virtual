# Recordatorios interpretados con confirmación

Esta opción experimental permite **proponer** recordatorios no reconocidos por
el enrutador tradicional. No modifica el modelo ni permite que éste guarde datos.
La escritura usa exclusivamente `crear_recordatorio` y su persistencia existente.

## Activación e independencia

Las opciones se leen al iniciar EVA. Sólo el valor exacto `1` las activa.

| `EVA_INTELIGENCIA_FALLBACK` | `EVA_INTELIGENCIA_RECORDATORIOS` | Solicitudes no atendidas tradicionalmente |
|---|---|---|
| Apagado | Apagado | Comportamiento anterior, Gemini opcional |
| `1` | Apagado | Hora, fecha y ayuda locales |
| Apagado | `1` | Propuestas de recordatorio con confirmación |
| `1` | `1` | Primero consultas de lectura; después propuestas de recordatorio |

Los comandos tradicionales conservan prioridad en todos los casos. Por ejemplo,
`Recuérdame estudiar mañana a las 18:00` sigue usando la creación tradicional.
La confirmación nueva se exige para el camino inteligente, por ejemplo
`Avísame estudiar mañana a las 18:00`. Esta etapa no convierte todos los comandos
tradicionales en operaciones con confirmación.

El observador tiene su propia variable `EVA_DIAGNOSTICO_INTELIGENCIA` y no decide
ni ejecuta acciones. Ninguna de estas opciones habilita nuevas alarmas,
aplicaciones o acciones de Spotify mediante predicciones.

## Arquitectura

1. La protección de órdenes compuestas actúa antes del enrutador y de las
   respuestas pendientes. Una orden compuesta no ejecuta ninguna de sus partes.
2. El mismo `SeguimientoAclaraciones` mantiene una sola conversación pendiente,
   tradicional o inteligente. Las entradas independientes descartan lo anterior.
3. Sólo si el enrutador no atendió la entrada se consultan los fallbacks activos.
4. `FallbackRecordatorios` reutiliza el trabajador, cola y plazos del fallback
   de lectura. Tiene activación, permisos y modelo cargado propios. Acepta sólo
   `crear_recordatorio` después de aplicar los umbrales oficiales sin cambios.
5. El contexto y los parámetros se validan con `contexto.py`, `seguridad.py`,
   `preparar_recordatorio` y el extractor existente, que reutiliza `tiempo_eva`.
   No se aceptan negaciones, condiciones, órdenes compuestas ni parámetros
   contradictorios como una duración mezclada con fecha/hora explícitas.
6. La propuesta y su fecha base quedan únicamente en memoria. El enrutador
   muestra la tarea y la fecha/hora completas en la zona local del equipo y
   pide confirmación. El extractor y el trabajador carecen de ejecutores.
7. Un «sí» inequívoco consume una propuesta vigente y completa. Antes de escribir
   se vuelven a comprobar el esquema, el futuro de la fecha y la validez de la
   hora local. Se llama al mismo `guardar_recordatorio_validado` que usa el
   enrutador tradicional, que a su vez llama a `crear_recordatorio`.

No se modifican `recordatorios.py`, `persistencia.py`, el formato del JSON ni la
recuperación de datos corruptos. Los recordatorios existentes se conservan.

## Estados y aclaraciones

| Estado | Comportamiento |
|---|---|
| `esperando_informacion` | Pregunta por datos faltantes o ambiguos; cero escrituras |
| `esperando_confirmacion` | Resume tarea, fecha y hora completas; cero escrituras |
| `confirmado` | Consentimiento consumido una vez; se intenta guardar y se informa el resultado real |
| `cancelado` | Se descarta la propuesta; cero escrituras |
| `caducado` | Ha vencido el plazo o la fecha propuesta ya pasó; cero escrituras |

El plazo es de **120 segundos desde que se registra la primera propuesta** y no
se renueva al aclarar datos. Se usa un reloj monotónico para la caducidad y el
reloj local de Windows para las fechas. Las fechas relativas conservan la base
de la solicitud durante el intercambio, incluso si cruza medianoche. El resumen
final siempre muestra una fecha absoluta y una hora de 24 horas.

Ejemplo:

```text
Usuario: Avísame estudiar mañana a las seis.
EVA: ¿De la mañana o de la tarde? ... Todavía no guardaré nada.
Usuario: De la tarde.
EVA: ¿Confirmas guardar el recordatorio «estudiar» el [fecha completa]
     a las 18:00, hora local del equipo? ... Todavía no está guardado.
Usuario: Sí.
EVA: De acuerdo. Te recordaré estudiar el [fecha] a las 18:00.
```

Sin una fecha, no se asume hoy. Sin período, «a las seis» no se transforma en
06:00. Sin tarea no se inventa una descripción. Las respuestas admiten formatos
acotados: `fecha: mañana`, `hora: 18:00`, `a las seis`, `de la tarde`,
`tarea: estudiar` cuando falte la tarea. Si ya hay datos y se quieren corregir,
usar `el recordatorio es: avísame estudiar mañana a las 18:00`; esta sustitución
se vuelve a validar y exige confirmación final. No se concatena libremente una
nueva orden a la propuesta.

«Sí» mientras faltan datos no autoriza nada. «Cancelar» o «no» descarta lo pendiente.
Una entrada independiente como «dime la hora» conserva su procesamiento tradicional
y no confirma el recordatorio. Una nueva petición tradicional de recordatorio
conserva también su comportamiento tradicional. Una orden compuesta rechazada
no consume la propuesta, que continúa sujeta al plazo original.

## Corrección de los casos manuales A y B

La reproducción aislada confirmó que ambas frases llegaban al servicio de
recordatorios inteligentes, pero terminaban en Gemini sin dejar una solicitud
pendiente. El modelo **sí** aceptaba `crear_recordatorio`: puntuación 0,4966 para
«necesito que mañana a las seis de la tarde me avises que debo estudiar Python»
y 0,5180 para «necesito que me recuerdes revisar un ejercicio», sin cambiar sus
umbrales. No era un rechazo del clasificador por faltar fecha u hora.

El bloqueo estaba en la validación contextual posterior, que no contemplaba
«me avises»/«me recuerdes». En A también fallaba el prefijo del extractor al
intercalarse la fecha y hora. En B el extractor podía pedir la fecha ausente,
pero la validación anterior impedía alcanzarlo. «Sí» y «Cancelar» no tenían
ninguna propuesta o aclaración que consumir; esos mecanismos no se sustituyeron.

La corrección se limita a `propuestas_recordatorios.py`: después de aceptar la
predicción sobre el texto original y comprobar su seguridad, adapta peticiones
explícitas «necesito/quiero que ... me avises/recuerdes ...» al prefijo `avísame`
del extractor existente. El contenido intercalado debe ser exclusivamente
temporal, comprobado con el mismo parser; no se descartan palabras desconocidas.
Se conserva la tarea y se sitúa el tiempo al final para reutilizar la aclaración
AM/PM existente. Reconocer la sintaxis de una hora ambigua no elige AM ni PM.

- A produce una propuesta con «debo estudiar python», mañana a las 18:00,
  sin escritura. Sólo «Sí» guarda una vez.
- B conserva «revisar un ejercicio» y pasa a `esperando_informacion`, sin
  parámetros de fecha/hora inventados. «Cancelar» descarta esa solicitud.
  También puede completarse con `fecha: mañana` y `hora: 18:00`, tras lo cual
  se exige una confirmación final.

No se modificaron el clasificador, sus umbrales, los validadores compartidos,
el enrutador, el seguimiento, el observador ni la persistencia durante esta
corrección. La independencia del observador implica que su interpretación
experimental puede seguir rechazando estas expresiones: el adaptador descrito
pertenece únicamente al flujo de propuestas inteligentes. No es una normalización
universal del español; otros órdenes de palabras o fragmentos temporales pueden
necesitar reformulación. Las aclaraciones conservan los formatos indicados arriba.

## Concurrencia, plazos y errores

- La propuesta se retira bajo el bloqueo de `SeguimientoAclaraciones`. Dos
  confirmaciones simultáneas no pueden recibir sus mismos parámetros.
- Un número de turno impide registrar una propuesta tardía si otro hilo ya
  recibió una entrada posterior. Los pasos de aclaración usan el mismo control.
- Los bloqueos conversacionales no abarcan voz, clasificación, Tkinter ni disco.
  La escritura conserva los bloqueos y el reemplazo atómico del almacén existente.
- Cada fallback tiene como máximo un trabajador reutilizable y cuatro peticiones
  en cola. La espera por clasificación está limitada a cinco segundos. Un
  resultado vencido se descarta y nunca tiene un callback de ejecución.
- La clasificación se espera desde el hilo de comandos existente, no desde el
  hilo de Tkinter. El cierre libera ambos servicios sin esperar una carga nativa.
- Si la escritura devuelve `False`, EVA informa que no pudo guardar; no anuncia
  éxito. Ante una excepción inesperada, pide revisar los recordatorios antes
  de volver a intentarlo. No reintenta automáticamente ni restaura el consentimiento.
- Si falla la entrega de la propuesta con una excepción observable, se descarta
  únicamente ese turno. Un fallo de carga del modelo desactiva su servicio hasta
  reiniciar, sin cambiar de modelo ni de permisos.
- Una propuesta pendiente tampoco se puede confirmar una vez cerrado o
  desactivado su servicio. Una escritura ya iniciada conserva la transacción
  existente; no se interrumpe a mitad del guardado.

`EVA_DIAGNOSTICO_COMANDOS=1` registra el recorrido `fallback_recordatorios` y el
estado de la propuesta. La preparación y la aclaración tienen cero acciones;
la confirmación registra la llamada real al ejecutor. `confirmado` indica
consentimiento, **no** garantiza almacenamiento: el contador y el mensaje de
resultado reflejan el éxito, fallo o resultado incierto del ejecutor.
No se añaden registros de audio, transcripciones, tareas ni datos personales en disco.

## Archivos de esta etapa

- `main.py`: conexión al final del enrutador, entrega de propuestas, confirmación
  y cierre del servicio; reutiliza el ejecutor tradicional.
- `aclaraciones_comandos.py`: estados inteligentes dentro del seguimiento existente,
  plazo compartido y consumo único de confirmaciones.
- `eva_inteligencia/fallback_lectura.py`: puntos de extensión del trabajador; sus
  permisos de lectura, ayuda determinista y activación permanecen iguales.
- `eva_inteligencia/fallback_recordatorios.py`: selección exclusiva de la intención
  de recordatorio usando el artefacto oficial y sus umbrales.
- `eva_inteligencia/propuestas_recordatorios.py`: preparación, aclaración y validación
  de propuestas sin acceso al almacenamiento.
- Este documento y pruebas locales ignoradas en `tests/`.

## Validación manual y límites

Reverificación al reanudar: **394 pruebas descubiertas, 393 aprobadas y una
omitida** (reentrenamiento), en 114,227 segundos. Se conservó la corrección
existente sin nuevos cambios de código. Informe local:
`tests/resultado_fallos_recordatorios_reanudacion.txt`.

Corrección A/B verificada: **394 pruebas descubiertas, 393 aprobadas y una
omitida** (reentrenamiento), en 96,529 segundos. Las 20 pruebas nuevas comprobaron
las frases exactas, los rechazos anteriores, propuesta sin escritura, confirmación
única, cancelación de solicitudes incompletas y completas, aclaración AM/PM,
caducidad no renovable, 24 confirmaciones concurrentes, fallos de persistencia,
rechazo de desconocidos y órdenes compuestas, lectura/observación independientes,
entradas de texto y transcripciones simuladas. Una prueba con almacenamiento
temporal real conservó un recordatorio sintético anterior y añadió A sólo tras
«Sí». Informe: `tests/resultado_fallos_recordatorios_regresion.txt`.

Las huellas de la revisión A/B confirman que las demás fuentes de aplicación,
el modelo oficial y el índice Git no cambiaron respecto al trabajo no publicado
que ya existía. Sólo se corrigió `propuestas_recordatorios.py`, se amplió este
documento y se añadieron pruebas/evidencias locales ignoradas en `tests/`.
`git diff --check` terminó sin errores. No se utilizó almacenamiento personal.

Verificación histórica de la integración inicial: **374 pruebas descubiertas, 373 aprobadas
y una omitida** (la histórica de reentrenamiento), en 106,894 segundos. El ejecutor
`tests/ejecutar_regresion_sin_entrenar.py` bloqueó los métodos de entrenamiento.
Informe local: `tests/resultado_recordatorios_inteligentes_final.txt`.

Se añadieron 34 pruebas específicas, incluidas propuestas sin escrituras,
confirmación única, cancelación, caducidad, información faltante, fechas pasadas,
ambigüedad AM/PM, contradicciones, 30 confirmaciones concurrentes, fallos de
persistencia, respuestas tardías, cierre y combinaciones de las dos opciones.
Las entradas de texto y las transcripciones simuladas usan el procesador real
con efectos sustituidos. Una prueba aislada utiliza el almacén real sólo en un
directorio temporal dentro de `tests/`: conserva un recordatorio sintético
anterior y verifica que un fallo de `os.replace` no modifica el archivo guardado.

Tkinter real, con ventana oculta, procesó diez pulsos de eventos mientras la
carga del modelo estaba detenida artificialmente; no se usó el micrófono real.
Las regresiones de hora, fecha, ayuda, observación, Whisper, persistencia y
eliminación de recordatorios vencidos aprobaron. Las huellas protegidas y el
índice Git permanecieron intactos, y `git diff --check` no informó errores.
Las pruebas y los experimentos continúan ignorados por Git.

```powershell
$env:EVA_INTELIGENCIA_RECORDATORIOS = "1"
$env:EVA_DIAGNOSTICO_COMANDOS = "1"
.venv\Scripts\python.exe main.py
```

Probar primero `Avísame estudiar mañana a las seis`, aclarar el período y cancelar.
Después probar una propuesta completa y confirmar sólo un recordatorio de prueba
que se desee guardar. Comprobar el resumen antes de decir «sí». Se puede desactivar
con el valor `0` y reiniciando EVA. El fallback de lectura se activa por separado.

Queda pendiente esta prueba con micrófono, síntesis de voz y aplicación completa.
El modelo conservador puede rechazar paráfrasis no cubiertas y las aclaraciones
requieren formatos explícitos. No se amplió el entrenamiento para cubrirlas.
Las propuestas sin confirmar se pierden al cerrar EVA y no se restauran al iniciar.
Si el proceso se cierra después de escribir y antes de anunciar éxito, comprobar
los recordatorios guardados antes de repetir la solicitud. No se añadió un nuevo
formato de identificadores persistentes ni una garantía transaccional entre voz y disco.
Con ambos fallbacks y el observador activos puede haber tres instancias del modelo;
el rendimiento conjunto con Whisper real queda para la validación manual.
