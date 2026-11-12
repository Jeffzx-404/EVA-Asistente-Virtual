# Persistencia: investigación de WinError 5

Base publicada: `53d1994`, rama `inteligencia-local-eva`. Se conservaron los
cambios locales de notificación sin bloqueo. No se usaron datos personales.

## Evidencia y causa reproducible

La operación que falló fue `os.replace(temporal, recordatorios.json)`: sustituía
el JSON activo, no el archivo `.lock` ni una copia de recuperación. En los
fallos instrumentados, los temporales estaban cerrados y no había lecturas
activas de EVA. Tanto origen como destino tenían atributos Windows `32`
(ARCHIVE), sin el atributo de sólo lectura. No se registró contenido ni rutas
en los informes técnicos nuevos.

Se confirmó una causa controlada que produce **el mismo WinError 5**:

- Abrir el destino con un lector Python `rb` que permanece abierto impide
  sustituirlo, tanto en el mismo proceso como en otro proceso de prueba.
- El bloqueo cooperativo `.lock` de EVA no puede impedir que un lector externo
  abra directamente el JSON sin participar en ese protocolo.
- Tras cerrar el lector, la misma sustitución funciona sin cambiar permisos.
- Un destino marcado como sólo lectura también devuelve error 5. Por eso el
  código no trata todo acceso denegado como una recuperación garantizada.

Los seis casos controlados (tres por versión) fallaron con error 5, conservaron
el original y limpiaron el temporal. Tras liberar el lector o restaurar el
atributo exclusivamente del archivo sintético, los seis permitieron sustituir.
Evidencia: `tests/winerror5_controlado_antes.json`.

Esto concuerda con el contrato Windows: un handle que no comparte
`FILE_SHARE_DELETE` restringe operaciones de eliminación/renombrado hasta su
cierre. Fuente primaria: [Microsoft, CreateFile](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew).

**Límite de la conclusión:** se reprodujo el mecanismo, pero no se identificó
el proceso o componente que ocasionó las denegaciones espontáneas. No se afirma
que fueran causadas por antivirus, indexación, sincronización u otro programa.

## Descriptores, bloqueos y directorios

`NamedTemporaryFile` termina su contexto después de `flush` y `fsync`, antes
del reemplazo. `_leer_bytes` usa `Path.read_bytes()`, que cierra el descriptor
antes de devolver los bytes. Las lecturas y modificaciones de recordatorios,
preferencias y personalización mantienen su transacción existente.

El `RLock` serializa los hilos de EVA; el bloqueo de un byte del archivo hermano
serializa procesos cooperantes. El nuevo guardia de avisos usa otro archivo:
ninguno mantiene abierto el JSON de destino. No se cambió ese protocolo ni se
añadieron lecturas del JSON fuera de sus transacciones.

Los temporales viven junto al destino, en el mismo volumen. La misma función
de escritura se utiliza para archivos activos, migraciones y copias de
recuperación; no se eliminan primero los destinos ni se usa copiar/borrar como
alternativa a la sustitución atómica.

Se compararon temporales bajo `tests/` con los del directorio temporal del
sistema. La muestra sin corregir en el segundo no presentó denegaciones. Esto
sugiere sensibilidad al entorno/ruta, pero no demuestra una causa de permisos.
No se cambiaron ACL, configuración de Windows ni protecciones de seguridad.
Se ejecutó en Windows/Python 3.13; no se ensayó Linux. `WinError` es específico
de Windows; otros sistemas también pueden denegar operaciones por sus propias
razones. Los reintentos nuevos sólo se aplican en Windows.

## Corrección limitada

Se modificó sólo `persistencia.py` respecto de la etapa anterior:

- Reintentar únicamente `os.replace` ante códigos Windows 5, 32 o 33.
- Máximo cinco intentos; pausas de 20, 50, 100 y 200 ms: 370 ms acumulados.
  Es un límite de espera añadida, no del tiempo que una llamada nativa de E/S
  pueda tardar. Las pausas conservan el bloqueo de la transacción.
- Reutilizar el **mismo temporal ya cerrado y sincronizado**, con los mismos
  bytes. No releer para reconstruir datos, repetir comandos, reemitir avisos
  ni añadir otra vez un recordatorio.
- No reintentar si se detecta un directorio o atributo de sólo lectura.
  Un acceso denegado permanente que no pueda distinguirse así agota el límite
  y conserva el error; no se alteran permisos ni atributos.
- Otros códigos y errores sin `winerror` no se reintentan.
- Si no se consigue sustituir, se propaga el fallo por el mecanismo existente;
  no se comunica éxito. Se mantiene la limpieza del temporal y el original.

No se cambian validación, formatos, migración, copias, confirmaciones ni la
política de reentrega tras un cierre entre aviso y retirada. El error transitorio
se tolera cuando desaparece dentro del presupuesto; no se promete eliminar la
causa externa ni superar bloqueos duraderos.

## Diagnóstico técnico opcional

`EVA_DIAGNOSTICO_PERSISTENCIA=1` habilita hasta 20 eventos por proceso en consola,
sólo cuando hay fallos de sustitución o una recuperación tras reintento.
Por defecto está desactivado; no crea registros en disco.

Cada evento contiene operación, resultado (`fallido`/`recuperado`), número de
intentos, `winerror`, `errno` y milisegundos. No contiene rutas, nombres de
archivos, transcripciones, textos de recordatorios, credenciales ni la excepción
cruda. Una consola cerrada o con error no cambia el resultado de persistencia.

## Mediciones y regresiones

Cada ensayo crea 80 entradas sintéticas mediante 12 hilos. Se comprueba que el
JSON contenga exactamente las escrituras confirmadas, sin pérdidas ni duplicados.
Cada versión se carga desde una copia temporal: no se restauró ningún archivo
del árbol de trabajo ni se cambió de rama.

| Versión / ubicación | Ensayos | Escrituras solicitadas | Fallos finales |
|---|---:|---:|---:|
| Publicada `53d1994`, temporales del proyecto | 20 | 1.600 | 2 |
| Notificaciones sin bloqueo, antes de esta corrección, proyecto | 20 | 1.600 | 3 |
| Antes de esta corrección, temporal del sistema | 20 | 1.600 | 0 |
| Corregida, proyecto, primera muestra | 20 | 1.600 | 0 |
| Corregida, proyecto, muestra ampliada | 60 | 4.800 | 0 |

En todas esas muestras se conservaron exactamente las escrituras confirmadas.
La frecuencia observada no es una estimación garantizada para otros equipos o
cargas. Evidencias locales: `tests/winerror5_base.json`,
`tests/winerror5_anterior.json`, `tests/winerror5_anterior_temporal.json` y
`tests/winerror5_corregido.json`.

La muestra ampliada registró **una denegación espontánea con WinError 5**, que
se recuperó mediante el reintento: no quedó ninguna escritura rechazada. En
conjunto, las muestras corregidas confirmaron **6.400 escrituras**, con cero
fallos finales, una denegación transitoria recuperada y ninguna pérdida ni
duplicado de entradas confirmadas. Evidencia adicional:
`tests/winerror5_corregido_extendido.json`. El campo `fallos` de ese JSON cuenta
intentos de `os.replace` fallidos (incluidos los recuperados), mientras que
`ensayos_fallidos` cuenta lotes con escrituras finalmente no confirmadas.

La regresión completa terminó con **471 pruebas aprobadas y una omitida**
(472 descubiertas, 109,476 segundos). La omitida requiere reentrenar, prohibido
en esta etapa. Pasaron las 12 pruebas nuevas de Windows junto con las anteriores
de notificaciones, concurrencia, persistencia e inteligencia local. No hubo
errores ni advertencias de Tkinter en esta ejecución. Evidencia:
`tests/resultado_winerror5_regresion.txt`.

La evidencia permite afirmar que se toleró el error transitorio observado sin
perder datos; no permite afirmar que se eliminó su causa externa ni que toda
denegación futura se recuperará.

Las pruebas controladas incluyen lector real en otro proceso, confirmación de
un aviso sin reemisión durante el reintento, lector/escritor concurrentes,
denegaciones permanentes, sólo lectura, limpieza de temporales, interrupción de
un proceso durante la espera, recuperación y diagnóstico limitado sin datos.
Las regresiones existentes cubren dos/cuatro procesos, JSON corrupto, cierres,
confirmaciones tardías y diálogo pendiente. Todo usa datos temporales y efectos
simulados; no se reentrenan modelos.

## Pendiente manual

Validar recordatorios sintéticos con el diálogo real abierto, creación desde otra
instancia, confirmación y cierre/reinicio. Si vuelve a aparecer la denegación,
recoger los códigos y número de intentos del diagnóstico y revisar qué proceso
mantiene el archivo abierto en ese momento. No desactivar protecciones para
ocultar el problema. Persisten la posible denegación permanente, bloqueos más
largos que el presupuesto y la reentrega tras caída antes de confirmar en disco.
