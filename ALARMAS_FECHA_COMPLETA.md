# Alarmas con fecha y hora completas

Corrección sobre `inteligencia-local-eva`, conservando los cambios pendientes
de auditoría y cierre basados en `d9da305`. No se publicaron cambios.

## Causa confirmada

La rama tradicional de `main.py` interpretaba sólo la hora con
`interpretar_hora` o recibía sólo hora/minuto de `interpretar_en_minutos`.
Nunca transmitía la fecha solicitada. `crear_alarma(hora, minuto, aviso)`
calculaba la siguiente ocurrencia de HH:MM: a las 07:00, la orden para mañana
a las 08:00 acababa programada para hoy. El diagnóstico confirmaba el registro
de una alarma, pero no la corrección de su fecha.

Texto y voz comparten `procesar_comando`; el defecto y su solución son comunes.

## Recorrido corregido

1. La misma rama tradicional llama a `interpretar_momento_alarma(texto, ahora)`.
2. El adaptador de `tiempo_eva.py` reutiliza `_momento`, el analizador temporal
   conservador existente de `eva_inteligencia.parametros`. No carga el modelo,
   no cambia sus umbrales y no ejecuta acciones.
3. Una fecha o duración explícita produce un `datetime` completo. Una fecha
   explícita pasada se rechaza; nunca se transforma en mañana. Se comprueba
   que todo el texto temporal sea reconocido, evitando ignorar fechas extra,
   períodos incompatibles o palabras desconocidas.
4. Sólo una hora sin fecha admite completar el día mediante la próxima
   ocurrencia futura. `de la mañana` es un período horario, no el día mañana.
   `08:00` se interpreta como formato de 24 horas. `a las ocho` sin período
   pide una fecha/hora inequívoca y repetir la instrucción completa: no guarda
   una alarma incompleta ni incorpora un diálogo nuevo de seguimiento.
5. El enrutador llama al ejecutor existente con
   `crear_alarma(hora, minuto, aviso, momento=fecha_hora)`.
6. El ejecutor valida tipo, concordancia de hora/minuto y fecha todavía futura,
   y conserva ese momento en el vigilante. No recalcula el día como próxima
   ocurrencia cuando se suministra `momento`.
7. La respuesta confirma **día/mes/año, HH:MM y hora local** sólo si el registro
   tuvo éxito. Si el tiempo vence antes del registro o falla el inicio del hilo,
   EVA no anuncia una alarma programada.

La interpretación y la comparación usan el reloj local de Windows. Un reloj
de entrada con zona se convierte primero a hora local; no se mezcla UTC con
horas locales. Se rechazan horas locales ambiguas o inexistentes por cambio
de horario. Las comprobaciones reales de cambios regionales/DST quedan para
validación manual; las pruebas no cambiaron la configuración de Windows.

Las duraciones conservan la fecha completa incluso al superar 24 horas. El
analizador existente redondea al siguiente minuto cuando hay segundos para no
avisar antes de cumplirse la duración. Para órdenes nuevas sin fecha, una hora
igual o anterior al instante de interpretación corresponde al día siguiente.

## Registro, compatibilidad y activación

No existe un archivo de alarmas ni interviene `persistencia.py`. Cada alarma
es un hilo vigilante con un vencimiento en su cierre de función, en memoria.
No se modificó ningún formato, no se migraron datos y no se inspeccionaron
alarmas personales.

La firma antigua de tres argumentos sigue admitida. Sus llamadores conservan
la semántica anterior de próxima ocurrencia de HH:MM, incluida la activación
en el minuto actual. La firma nueva añade un parámetro opcional por nombre;
no rompe llamadas anteriores. Los vigilantes ya creados conservan el momento
que tenían: no se reinterpretan ni se duplican al cambiar archivos de código.

El vigilante compara `datetime.now() >= vencimiento` con fecha y hora completas
y sale después de un aviso. Un retraso breve o la suspensión que atraviese el
minuto no pierde el vencimiento mientras el proceso siga vivo. La espera se
interrumpe mediante el evento de cierre cooperativo existente.

Cerrar/reiniciar EVA pierde las alarmas de esa sesión, como antes. Añadir
persistencia de alarmas sería otra función y no forma parte de esta corrección.
Los recordatorios persistentes y su recuperación no se tocaron.

## Archivos de esta etapa

- `tiempo_eva.py`: adaptador puro nuevo para el momento completo. Las funciones
  heredadas permanecen idénticas y los analizadores de recordatorios no cambian.
- `alarmas.py`: parámetro opcional `momento`, validación y registro de fecha completa.
- `main.py`: sustitución del cálculo que perdía la fecha dentro de la rama de
  alarmas; reutiliza el ejecutor y confirma el momento completo.
- Este documento y referencias de actualización en los informes anteriores.
- Pruebas y evidencias locales ignoradas en `tests/`.

No se modificaron Whisper Small, el modelo oficial, el observador, los fallbacks,
Spotify, Gemini, recordatorios ni los mecanismos de cierre. No se habilitaron
funciones experimentales ni intenciones nuevas mediante predicciones.

## Pruebas

Las pruebas de alarmas usan reloj, sonido, avisos y creación de hilos simulados;
una prueba usa un trabajador real sin sonido para comprobar la interrupción de
su espera. No hay almacenamiento de alarmas que sustituir: las regresiones de
persistencia usan sus directorios temporales existentes.

Casos: hoy/mañana antes y después de las 08:00, mañana a las 06:00, fechas
pasadas, hora futura/pasada sin fecha, cambio de mes/año, medianoche, duraciones
superiores a 24 horas, ambigüedad AM/PM, fechas completas, transcripción simulada,
reloj con zona, vencimiento exacto/retrasado, aviso único, firma heredada, cierre
del vigilante y fallo de registro sin éxito falso.

Se adaptaron legítimamente pruebas antiguas que esperaban una tupla sin fecha,
aceptaban `a las 5` sin aclaración o caracterizaban la pérdida de fecha como
defecto conservado. Las comprobaciones de huellas sólo exceptúan los archivos
autorizados; una nueva prueba conserva las demás fuentes, modelos e índice Git.
Otra compara el AST de los analizadores heredados y de las demás funciones de
`main.py` con la copia anterior a esta etapa.

Resultados finales: **445 pruebas aprobadas y una omitida** (446 descubiertas,
117,696 segundos). La omisión corresponde exclusivamente al reentrenamiento
histórico prohibido en esta etapa. No hubo fallos en la ejecución final.
Al retomar el trabajo se verificaron nuevamente las 16 pruebas específicas de
fecha de alarmas (0,847 segundos) y las 10 de cierre y destino de EVA
(1,710 segundos): todas aprobadas, sin nuevos cambios en código de ejecución.

Evidencias locales: `tests/resultado_fechas_alarmas_antes.txt`,
`tests/resultado_fechas_alarmas_despues.txt`,
`tests/resultado_fechas_alarmas_final.txt`,
`tests/resultado_fechas_alarmas_reanudacion.txt` y
`tests/resultado_cierre_reanudacion_alarmas.txt`.
El ejecutor `tests/ejecutar_regresion_sin_entrenar.py` bloquea
entrenamiento y omite únicamente la prueba histórica que requiere reentrenar.

## Validación manual pendiente

- Probar por texto y micrófono una alarma completa de prueba y comprobar la
  fecha **y** hora que EVA confirma, no sólo HH:MM.
- Verificar que hoy a una hora pasada se rechace y que `a las ocho` solicite
  aclaración sin programar nada.
- Comprobar un aviso real, detener su sonido, suspender/reanudar Windows
  atravesando el vencimiento y cerrar EVA durante la espera.
- Comprobar micrófono, altavoces, SAPI y cambios del reloj/zona de Windows en un
  entorno de prueba. Las simulaciones no certifican estos dispositivos ni una
  instalación empaquetada.

Riesgos conservados: el proceso debe seguir abierto para avisar; cambios del
reloj/zona afectan a la comparación local; una llamada de voz ya iniciada no
puede cancelarse de forma transaccional. No se añadieron garantías nuevas de
persistencia ni se rediseñó la coordinación de audio.
