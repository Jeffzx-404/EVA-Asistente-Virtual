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
3. Las consultas claras de ayuda descritas abajo se reconocen mediante una regla
   determinista de frase completa, con controles de seguridad y composición.
   Devuelve únicamente `ayuda`, sin cargar el modelo. Para las demás consultas,
   un trabajador carga una sola vez el modelo oficial de `modelos/` mediante
   `InterpreteLocal()`. No importa modelos experimentales ni asociaciones personales.
4. Para la vía del modelo se exige una propuesta aceptada por los umbrales existentes y se vuelven a
   comprobar contexto, seguridad, parámetros y permisos. Sólo se permiten
   `consultar_hora`, `consultar_fecha` y `ayuda`, con parámetros exactamente vacíos.
5. Tanto la regla como el trabajador devuelven únicamente el nombre autorizado. `main.py` usa un
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
por sus umbrales o contexto. La regla de ayuda descrita abajo es independiente de
esa predicción; los umbrales no se relajaron para ampliar la cobertura.

## Ayuda local determinista

Corrección posterior a `1bc55c1`: «Eva, explícame qué cosas sabes hacer» era
rechazada **antes de puntuar con el modelo**, por `analizar_contexto` como
`pregunta_externa`. El validador específico de ayuda también la consideraba
incompatible. Por ello no se alcanzaba `responder_funciones_disponibles` y el
enrutador continuaba hacia Gemini. Se reprodujo con el código anterior.

El fallback habilitado reconoce ahora estas consultas completas, tolerando
mayúsculas, tildes, puntuación, el vocativo EVA y «por favor» en los extremos:

- «Explícame tus funciones».
- «Explícame qué cosas sabes hacer» (también sin «cosas»).
- «Qué puedes hacer por mí, EVA» (también sin «por mí»).
- «Cuáles son tus funciones».
- «Qué comandos tienes disponibles».

La segunda persona y la coincidencia de toda la frase delimitan el contexto de
ayuda sobre EVA. No se buscan palabras sueltas como «funciones» en preguntas
generales ni se eliminan partes desconocidas. Se reutilizan la normalización,
el control de seguridad y la protección de órdenes compuestas. Las negaciones,
condiciones, peticiones incompletas y órdenes adicionales no se aceptan por esta
regla. Las preguntas generales siguen por la vía anterior, con Gemini opcional.

Se reutiliza **sin cambios** `responder_funciones_disponibles`, que informa de
hora, fecha, aplicaciones compatibles, alarmas, recordatorios y música en Spotify
cuando esté configurado, y de preguntas con Gemini si está habilitado. No abre
aplicaciones ni llama a esos servicios al describirlos. No promete funciones de
un asistente genérico ni habilita más permisos.

Con `EVA_DIAGNOSTICO_COMANDOS=1`, una de estas consultas muestra ruta `fallback`,
intención `ayuda`, `fallback_consultado=true` y una ejecución confirmada. La
consulta al fallback no implica que haya sido necesario cargar el clasificador.
El modo observación permanece independiente y puede seguir mostrando
`desconocido`/`fuera_de_alcance` para la misma frase: informa de su análisis
experimental, no de la ruta ejecutada ni de esta regla determinista.

La regla se evalúa después de comprobar activación, prioridad tradicional y
cierre. No crea trabajadores, escribe archivos ni guarda textos. Si falla su
validación, devuelve control al comportamiento general. El resto de consultas
mantiene los límites de cola y espera del modelo. El fallback continúa apagado
por defecto; un servicio cerrado por un fallo anterior de carga sigue cerrado
hasta reiniciar EVA.

## Concurrencia y fallos

- El trabajador daemon se crea únicamente ante la primera consulta que necesite
  el modelo con la opción activada. La ayuda determinista no lo necesita.
  Desactivada, no crea hilos ni carga sklearn o el modelo.
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
- «Explícame tus funciones» y «Eva, explícame qué cosas sabes hacer».

Comprueba una sola respuesta, hora/fecha correctas y ventana sensible. «Dime la
hora» debe seguir usando la ruta tradicional. El observador puede activarse con
su propia variable; sus líneas de consola no deben añadir respuestas de voz.

Para comparar con el comportamiento anterior, cierra EVA, establece
`$env:EVA_INTELIGENCIA_FALLBACK = "0"` y reinicia. La opción no se guarda de forma
permanente. Las pruebas de órdenes con efectos se realizaron con simulaciones;
no usar comandos reales no deseados para verificar el rechazo del fallback,
porque el enrutador tradicional conserva su prioridad.

## Verificación automatizada

Corrección de ayuda local, verificada nuevamente al reanudar: **339 pruebas
aprobadas y 1 omitida**, de 340 descubiertas, en 115,255 segundos. Se omite
únicamente la prueba histórica de reentrenamiento; los métodos de entrenamiento
permanecen bloqueados. Informe local: `tests/resultado_ayuda_local_reanudacion.txt`.

Incluye 16 pruebas específicas de ayuda: comparación con el fallback anterior,
las cinco expresiones y sus variantes, ruta de ejecución y respuesta única,
preguntas generales sobre IA, negaciones, frases incompletas y compuestas,
prioridad tradicional, fallback apagado, observación independiente y las dos
consultas de hora/fecha confirmadas por el usuario. También se verificaron 60
consultas concurrentes de ayuda, fallos de validación y carga innecesaria del
modelo evitada. Los efectos externos se simularon; no se crearon recordatorios
personales ni se reprodujo música.

La corrección modifica únicamente `eva_inteligencia/fallback_lectura.py` y este
documento entre los archivos versionados. Se añadieron pruebas y copias de
referencia locales, y se adaptaron las comprobaciones históricas al commit
publicado por el usuario. `tests/` y `experimentos/` continúan ignorados. Las
huellas verifican que `main.py`, el modelo oficial, Whisper, el observador, alarmas,
recordatorios y el índice Git permanecen intactos. `git diff --check` sin errores.
No hubo que añadir más cambios de lógica al reanudar: se conservaron la regla y
las pruebas ya implementadas, se repitió la regresión y se cerró esta documentación.

Resultado histórico de la primera etapa del fallback: **301 pruebas aprobadas y 1 omitida**, de 302 descubiertas,
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
