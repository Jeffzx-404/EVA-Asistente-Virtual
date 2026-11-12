# Auditoría y estabilización de EVA

Actualización posterior: véanse las correcciones específicas de
[cierre](VERIFICACION_CIERRE_ALARMAS.md) y [fecha de alarmas](ALARMAS_FECHA_COMPLETA.md).
Se conservan aquí los hallazgos y resultados originales de la auditoría.

Base revisada: `d9da305`, rama `inteligencia-local-eva`. El árbol estaba limpio
al comenzar. No se modificaron datos personales ni se publicaron cambios.

## Alcance y método

Revisión de `main.py`, `interfaz.py`, `whisper_control.py`, `comandos_voz.py`,
`aclaraciones_comandos.py`, `recordatorios.py`, `persistencia.py`, `preferencias.py`,
`alarmas.py`, `spotify_control.py` y `gemini_control.py`. En `eva_inteligencia/`
se revisaron especialmente los trabajadores de observación/fallback, el modelo
oficial, la integración, el contexto, los parámetros y las propuestas.

Se reprodujeron defectos antes de corregirlos. Las pruebas ejecutan funciones
reales del enrutador extraídas por AST, con aplicaciones, voz y servicios
simulados; no importan el arranque de `main.py`. La persistencia utiliza
directorios temporales y datos sintéticos. Las pruebas gráficas usan Tkinter
real con ventana oculta, sin interacción con micrófono ni altavoces reales.

## Problemas confirmados y correcciones

| Hallazgo | Gravedad | Causa y resultado |
|---|---|---|
| Borrado por mencionar una orden | Alta | `No quiero borrar todos los recordatorios` y preguntas sobre cómo borrarlos invocaban el ejecutor. Había dos ramas equivalentes con búsqueda de subcadenas. Se conserva una sola, que exige una orden completa explícita. |
| Otros efectos por coincidencia parcial | Alta | Negaciones iniciales podían abrir aplicaciones; menciones de alarmas con duración podían programarlas y menciones de controles musicales podían accionarlos. Se rechazan negaciones iniciales después del seguimiento de aclaraciones; alarmas requieren un prefijo de orden y los controles musicales una frase completa. Los títulos explícitos se atienden antes. |
| Despedida sin cierre | Media | `procesar_comando` devolvía `False`, pero texto y voz ignoraban el resultado. Además, `cerrar EVA` perdía el destino al retirar el vocativo final. Los adaptadores ahora solicitan el cierre sólo ante `False` y la interfaz lo despacha por su cola en Tk. Se reconoce ese destino sin cambiar el normalizador compartido. Mencionar una despedida no cierra EVA. |
| Alarma perdida tras saltar un minuto | Alta | El vigilante exigía igualdad de hora y minuto. Una simulación de suspensión saltó de 09:59:59 a 10:01 sin avisar a las 10:00. Se fija el próximo vencimiento completo al crear la alarma y se comprueba `ahora >= vencimiento`. Sigue siendo una alarma en memoria, de una sola entrega. |
| Vigilantes sin señal de cierre | Media | Alarmas y recordatorios seguían sus bucles mientras se cerraban otros servicios. Se añadieron señales de parada y esperas interrumpibles, conectadas al cierre. No se interrumpe a mitad una transacción ni se confirma un aviso omitido por cierre. |
| Fallos de voz/consola abortan recursos o avisos | Media | `runAndWait` podía omitir `stop` al fallar. Los iconos de alarma provocaban `UnicodeEncodeError` con consola cp1252; la impresión previa a hablar también podía abortar la respuesta. Se garantiza `stop` tras `runAndWait` y se toleran errores de consola en esos puntos. Voz, velocidad, volumen y Whisper no se cambian. |
| «Canción anterior» interceptada | Media | Se consideraba una respuesta de título aunque no existiera aclaración pendiente. Ahora llega al control tradicional cuando no hay pendiente. Si EVA está solicitando un título, conserva su significado de respuesta. |

No se añadieron funciones, intenciones ejecutables ni permisos del clasificador.
Las correcciones del enrutador son deterministas; no utilizan predicciones para
autorizar estas acciones. La protección de órdenes compuestas sigue ejecutándose
antes de las ramas tradicionales. Los casos de recordatorios inteligentes A/B,
el consentimiento explícito, la caducidad de 120 segundos y el consumo único no
se modificaron.

## Archivos modificados

- `main.py`: reconocimiento y cierre descritos, tolerancia de consola y limpieza
  de voz; conexión de señales de parada. No se sustituyó el enrutador.
- `interfaz.py`: solicitud de cierre mediante la cola existente.
- `alarmas.py`: vencimiento completo, parada cooperativa y consola segura.
- `recordatorios.py`: parada cooperativa del vigilante. El ciclo de entrega,
  retirada y persistencia conserva sus transacciones.
- `aclaraciones_comandos.py`: desambiguación de `Canción anterior` sin pendiente.
- Este informe.
- Pruebas y evidencias locales en `tests/`, ignoradas por Git. No se cambiaron
  archivos de `experimentos/`.

## Verificación automatizada

Base: **394 pruebas descubiertas; 391 aprobadas, dos fallos y una omitida**.
Los dos fallos comparaban `.git/index` con una huella anterior a la publicación
de `d9da305`; no eran fallos funcionales. Se conservó una nueva huella al inicio
de esta auditoría para comprobar que el índice permanece intacto.

Las pruebas históricas que congelaban archivos ahora autorizados a cambiar se
ajustaron únicamente para esos archivos. No se alteraron sus artefactos ni los
informes históricos. La nueva prueba de integridad comprueba las demás fuentes,
los modelos y el índice respecto al inicio de esta etapa. Los contratos de
captura de Whisper y paridad de predicciones se mantienen.

Pruebas nuevas: **26 aprobadas** en la ejecución específica (2,527 segundos).
Incluyen cierre por texto/voz, Tk sensible durante la liberación, suspensión
simulada, cierre de vigilantes, errores de voz/consola, negaciones, menciones
sin autorización, controles musicales explícitos, propuestas sólo en memoria e
integridad. Una de ellas caracteriza un riesgo conservado del bloqueo global;
su aprobación no significa que ese riesgo esté corregido.

Resultado final: **420 pruebas descubiertas, 419 aprobadas y una omitida**, en
**111,361 segundos**, con código de salida 0. Incluye las 26 pruebas nuevas.
El ejecutor `tests/ejecutar_regresion_sin_entrenar.py` bloquea los métodos de
entrenamiento y omite únicamente la prueba histórica que reentrena.

`git diff --check` terminó sin errores (sólo avisos de conversión LF/CRLF).
`git ls-files tests eva_inteligencia/experimentos` no devuelve archivos:
ambas carpetas siguen fuera del índice. No se ejecutaron operaciones de
staging, commit, push ni merge. La rama `main` permanece intacta.

Evidencias locales:

- `tests/resultado_auditoria_base.txt`
- `tests/resultado_auditoria_reproduccion.txt`
- `tests/resultado_auditoria_cierre_alias_antes.txt`
- `tests/resultado_auditoria_borrado_antes.txt`
- `tests/resultado_auditoria_coincidencias_antes.txt`
- `tests/resultado_auditoria_cancion_anterior_antes.txt`
- `tests/resultado_auditoria_especificas.txt`
- `tests/resultado_auditoria_final.txt`

Las regresiones existentes incluyen JSON truncado/estructura incorrecta,
permisos simulados, fallos de reemplazo atómico, migración, concurrencia de
hilos/procesos, creación durante avisos y reinicios reales en subprocesos con
almacenes temporales. También verifican confirmación única, cancelación,
caducidad, resultados tardíos, fallback encendido/apagado, carga sin experimentos
y observación independiente. No se probaron servicios externos reales.

## Riesgos conservados y cambios de mayor alcance

1. **Bloqueo prolongado del almacén durante avisos — confirmado, gravedad media.**
   `revisar_recordatorios` mantiene la transacción mientras espera el aviso
   visual. `persistencia` usa un bloqueo de hilos global: una prueba temporal
   confirmó que incluso una escritura de preferencias espera hasta cerrar el
   aviso. Tk sigue atendiendo eventos, pero esos comandos pueden esperar
   indefinidamente al usuario. No se retiró ese bloqueo: garantiza exclusión
   entre vigilantes y evita duplicados. Resolverlo correctamente requiere
   separar entrega y confirmación mediante un protocolo de identificación y
   reserva que cubra también procesos, reinicios y fallos. Ese cambio de mayor
   riesgo queda documentado, sin alterar el formato de los datos en esta etapa.
2. **Cierre cooperativo, no cancelación total.** Las señales detienen futuras
   revisiones y despiertan esperas. No pueden abortar llamadas ya iniciadas a
   SAPI, servicios externos o controladores de audio. El modelo del observador
   y fallbacks puede terminar una inferencia nativa como daemon, descartando su
   resultado. No se añadió una cancelación transaccional de todos los comandos
   en curso; cerrar mientras una acción ya está ejecutándose necesita validación
   manual y puede requerir un diseño más amplio.
3. **Voz y captura simultáneas — pendiente de validación acústica.** El bloqueo
   actual serializa voces, pero no coordina completamente reproducción y
   micrófono. No se afirma haber probado eco, autorreconocimiento ni SAPI real.
4. **Entrega frente a cierre inesperado.** Si EVA termina después de mostrar un
   recordatorio y antes de confirmar su retirada en disco, puede volver a
   avisar al reiniciar. Se mantiene la política de preferir repetición a pérdida.
   Un error de guardado también puede producir reentrega controlada. Las
   propuestas no confirmadas viven sólo en memoria y desaparecen al reiniciar.
5. **Límites del enrutador.** Las reglas siguen siendo léxicas. Las pruebas no
   demuestran comprensión universal de negaciones indirectas, citas o
   condiciones. Quedan otras ramas tradicionales con coincidencias parciales;
   no se reemplazó todo el enrutador ni se amplió el modelo para resolverlas.
6. **Alarmas en memoria.** Se recupera un vencimiento saltado mientras EVA sigue
   abierta, no una alarma después de terminar el proceso. Persistir alarmas
   sería una función nueva y queda fuera de alcance.

## Pruebas manuales y preparación para Windows

Antes de publicar:

1. Con micrófono y altavoces reales, comprobar dictado mientras EVA habla,
   despedida por voz, cierre desde la ventana y desaparición de procesos.
2. Repetir los recordatorios A/B: propuesta sin guardar, «Sí» una vez,
   aclaración de fecha/hora, cancelación y caducidad. Utilizar sólo recordatorios
   de prueba que se desee conservar; comprobar el resumen antes de confirmar.
3. Entregar un recordatorio vencido, cerrar/reabrir EVA y verificar que no
   reaparece tras confirmar el aviso. Revisar también cerrar con el aviso abierto.
4. Programar una alarma de prueba, suspender/reanudar Windows cruzando su minuto,
   detenerla y cerrar EVA durante el aviso.
5. Verificar Spotify y Gemini con cuentas autorizadas: conexión, desconexión,
   falta de red, reproducción/pausa y cierre durante una petición. Las pruebas
   automatizadas no accedieron a cuentas ni validan respuestas actuales del servicio.

**Evaluación:** se puede comenzar una prueba técnica de empaquetado aislada;
todavía no se certifica una distribución instalable estable. Además de la
validación anterior, el arranque del trabajador Whisper usa actualmente
`sys.executable` más la ruta de `whisper_control.py`; un ejecutable congelado
necesita un despacho explícito de trabajador y verificación de que no vuelve a
abrir EVA. No se modificó Whisper ni se construyó un instalador en esta etapa.
También deben verificarse inclusión del modelo oficial, compatibilidad exacta
de scikit-learn, dependencias nativas/audio, datos en LOCALAPPDATA y actualización
sin pérdida de datos en una instalación limpia. No iniciar publicación todavía.
