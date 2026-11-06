# Fallback experimental para consultas de lectura

Desactivado por defecto. Sólo el valor exacto `EVA_INTELIGENCIA_FALLBACK=1`, leído
al iniciar EVA, habilita el fallback. No se cambian preferencias ni la variable
independiente `EVA_DIAGNOSTICO_INTELIGENCIA` del observador.

## Recorrido de una consulta

1. El enrutador tradicional conserva todas sus ramas y su prioridad, incluidas
   las aclaraciones pendientes, respuestas personales y consultas reconocidas.
2. Sólo su última rama, antes de Gemini, declara `tradicional_reconocido=False`
   y consulta el fallback. No se utiliza el retorno ambiguo `None` de otros
   comandos para decidir si fueron reconocidos.
3. Un trabajador carga una sola vez el modelo oficial de `modelos/` mediante
   `InterpreteLocal()`. No importa modelos experimentales ni asociaciones personales.
4. Se exige una propuesta aceptada por los umbrales existentes y se vuelven a
   comprobar contexto, seguridad, parámetros y permisos. Sólo se permiten
   `consultar_hora`, `consultar_fecha` y `ayuda`, con parámetros exactamente vacíos.
5. El trabajador devuelve únicamente el nombre autorizado. `main.py` usa un
   diccionario fijo de tres funciones; no ejecuta código ni resuelve nombres
   arbitrarios. El resultado del modelo no se convierte en una orden de Windows.
6. Una consulta atendida termina esa rama: no se llama a Gemini ni se da una
   segunda respuesta. Si no se acepta, el enrutador conserva su consulta general
   a Gemini, que sigue siendo opcional y sin herramientas ejecutoras.

La hora y fecha usan el reloj local de Windows en el momento de responder. Las
funciones `responder_hora_actual` y `responder_fecha_actual` contienen las mismas
respuestas que las ramas tradicionales, que ahora también llaman a esas funciones.
No había un ejecutor de ayuda: se añadió `responder_funciones_disponibles`, una
respuesta fija que describe capacidades existentes y sus servicios opcionales.

## Permisos y límites

El fallback no permite aplicaciones, alarmas, recordatorios, Spotify, escritura
de preferencias ni otros archivos personales. Tampoco acepta negaciones, órdenes
compuestas, referencias personales o solicitudes ambiguas rechazadas por los
validadores. Las consultas desconocidas conservan la ruta general; rechazarlas
para ejecución local no significa bloquear una respuesta informativa de Gemini.

Esta protección se aplica al fallback. Los comandos tradicionales reconocidos
conservan su ejecución previa y no son reevaluados por él. El observador sigue
siendo sólo diagnóstico: no comparte callbacks, estado ni resultados con el
fallback y no produce respuestas de voz.

No se entrenó ni ajustó el clasificador. Algunas formulaciones siguen rechazadas
por sus umbrales o contexto. Por ejemplo, «Explícame tus funciones» se acepta en
las pruebas, mientras que «Qué puedes hacer» no supera actualmente los umbrales.
No se relajaron para ampliar la cobertura.

## Concurrencia y fallos

- El trabajador daemon se crea únicamente ante la primera consulta no reconocida
  con la opción activada. Desactivada, no crea hilos ni carga sklearn o el modelo.
- Hay una cola de cuatro peticiones pendientes y como máximo una en análisis.
  La cola llena no crea más trabajadores: esa consulta continúa por la ruta general.
- La espera máxima por petición es de cinco segundos, incluida la primera carga.
  La espera sucede en los hilos de comandos ya existentes, nunca en los callbacks
  de Tkinter. La ventana continúa procesando sus eventos.
- El trabajador nunca responde ni ejecuta funciones. Un resultado vencido se
  descarta y no puede producir una respuesta local después de la respuesta general.
- Una carga fallida desactiva ese trabajador hasta reiniciar EVA, sin cambiar de
  modelo ni descargar nada. Una excepción de inferencia rechaza esa petición y
  permite intentar la siguiente.
- Cerrar EVA libera las esperas y la cola sin esperar a una inferencia nativa.
  El trabajador daemon no mantiene abierta la aplicación. No se guardan textos
  ni se añade un servicio externo para analizar las consultas.

## Prueba manual antes de publicar

En PowerShell, desde el proyecto:

```powershell
$env:EVA_INTELIGENCIA_FALLBACK = "1"
.venv\Scripts\python.exe main.py
```

Prueba por texto y voz:

- «Me dices la hora» o «Necesito saber la hora».
- «Me dices la fecha de hoy» o «Qué día de la semana es hoy».
- «Explícame tus funciones».

Comprueba una sola respuesta, hora/fecha correctas y ventana sensible. «Dime la
hora» debe seguir usando la ruta tradicional. El observador puede activarse con
su propia variable; sus líneas de consola no deben añadir respuestas de voz.

Para comparar con el comportamiento anterior, cierra EVA, establece
`$env:EVA_INTELIGENCIA_FALLBACK = "0"` y reinicia. La opción no se guarda de forma
permanente. Las pruebas de órdenes con efectos se realizaron con simulaciones;
no usar comandos reales no deseados para verificar el rechazo del fallback,
porque el enrutador tradicional conserva su prioridad.

## Verificación automatizada

Resultado final: **301 pruebas aprobadas y 1 omitida**, de 302 descubiertas,
en 50,744 segundos. Se añadieron 25 pruebas (24 de fallback y una de carga sin
experimentos). Registro local: `tests/resultado_fallback_regresion.txt`.
`git diff --check` terminó sin errores.

Se usaron el modelo oficial real, reloj fijo y ejecutores/servicios simulados.
Se comprobaron las tres consultas, prioridad tradicional, denegación de otras
intenciones, ausencia de duplicados, Gemini informativo, observación simultánea,
cola llena, carga fallida, excepciones, cierre y descarte de resultados tardíos.
Tkinter real con ventana oculta mantuvo sus eventos mientras la carga simulada
del fallback estaba detenida. Una copia aislada sin `experimentos/` comprobó la
carga desde otro directorio y el rechazo de acciones no permitidas, sin Internet.

La regresión se ejecuta con `tests/ejecutar_regresion_sin_entrenar.py`, que bloquea
los métodos de entrenamiento y omite la prueba histórica que reentrena. Las
comprobaciones históricas de fuentes usan copias anteriores para los cambios
autorizados; se verifican nuevamente los hashes del modelo, Whisper, observador,
fuentes protegidas e índice de Git al inicio de esta etapa.

Archivos de aplicación modificados: `main.py` y el módulo nuevo
`eva_inteligencia/fallback_lectura.py`; este documento describe su uso. Las pruebas
y sus adaptaciones permanecen dentro de `tests/`, ignorado por Git. No se
modificaron el modelo, sus umbrales, Whisper Small, la interfaz, Gemini, Spotify,
las alarmas, los recordatorios ni la persistencia.

Queda pendiente repetir estas consultas con micrófono, síntesis de voz y ventana
visible en la aplicación completa. La prueba automatizada de interfaz no mide
el rendimiento conjunto de todos los servicios ni garantiza latencia constante.
