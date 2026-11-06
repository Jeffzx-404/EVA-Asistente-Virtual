# Protección de instrucciones compuestas

La protección tradicional está siempre activa. No requiere el clasificador ni
`EVA_INTELIGENCIA_FALLBACK=1`. El fallback sigue desactivado por defecto y sólo
autoriza las tres consultas de lectura previamente implementadas.

## Causa confirmada

En la versión anterior, `procesar_comando` comprobaba la hora **antes** de abrir
Spotify. La regla del reloj exige coincidencia de la frase completa, por lo que
«Eva, dime la hora y abre Spotify» no coincidía. Más adelante, la condición
`"abre spotify" in comando` coincidía con una parte y abría Spotify. No llegaba
al fallback ni a Gemini. El observador analiza en paralelo, sin vetar acciones;
la validación contextual del fallback sólo se aplica cuando se llega a él.

La prueba con la copia anterior del procesador y ejecutores simulados reproduce
una llamada a `abrir_aplicacion('spotify')` y cero llamadas al fallback/Gemini.

## Corrección

- `ordenes_compuestas.py` reutiliza la segmentación léxica de `contexto.py`, sin
  cargar modelos, entrenar ni ejecutar funciones. Exige otra solicitud reconocible,
  no sólo la presencia de «y». También detecta aplicaciones coordinadas.
- `main.py` comprueba las órdenes compuestas antes de las ramas tradicionales,
  las respuestas personalizadas y el consumo de una aclaración pendiente.
  Ante varias solicitudes, pide una sola y no ejecuta ninguna parte.
- El rechazo conserva la aclaración pendiente hasta que se responda, cancele o
  caduque conforme a sus reglas existentes. No renueva su caducidad.
- «Reproduce Ella y yo» y nombres con puntuación conservan su ruta musical.
  Para títulos que parecen órdenes, se admite un literal explícito, por ejemplo
  `Reproduce la canción «Dime la hora y abre Spotify»`. Se reutiliza el ejecutor
  musical existente; las palabras del título no pasan por las ramas de apertura.
  Una instrucción añadida **fuera** de las comillas sigue siendo rechazada.
- Las aclaraciones musicales aceptan ese mismo formato de título literal.

## Diagnóstico opcional de rutas

En PowerShell, antes de iniciar EVA:

```powershell
$env:EVA_DIAGNOSTICO_COMANDOS = "1"
.venv\Scripts\python.exe main.py
```

Para desactivarlo: `$env:EVA_DIAGNOSTICO_COMANDOS = "0"`. No depende de los
indicadores del observador ni del fallback y no se guarda en preferencias.

Se emite una línea JSON por interacción en la consola. Incluye identificador,
texto normalizado limitado a vocabulario estructural público, ruta y recorrido,
intenciones detectadas cuando corresponde, motivo de rechazo, llamadas a
ejecutores y consulta al fallback habilitado. El texto libre (títulos, asuntos,
nombres, números, etc.) se sustituye por un marcador; no se registran argumentos,
resultados privados ni detalles de excepciones. No se crean archivos de registro.
Esta variable no cambia las salidas de los otros diagnósticos independientes.

Las trazas usan `ContextVar` para separar interacciones concurrentes. No añaden
hilos ni respuestas de voz. Un fallo al imprimir no interrumpe el comando.

Los contadores se obtienen al llamar realmente a los ejecutores:

- `ejecutores_invocados`: llamadas realizadas, incluso si fallan.
- `acciones_confirmadas`: ejecutores que devuelven éxito explícito.
- `acciones_fallidas`: devuelven fallo explícito.
- `errores_ejecutores`: lanzan una excepción; su efecto queda sin confirmar,
  porque la excepción podría haberse producido después de una acción externa.
- `acciones_sin_confirmar`: el ejecutor antiguo no ofrece confirmación fiable.
- `acciones_ejecutadas`: éxitos confirmados; `null` si hay resultados inciertos.

La apertura de aplicaciones confirma que Windows aceptó la llamada de apertura,
no que la ventana sea visible. Los ejecutores antiguos sin confirmación conservan
su comportamiento y se indican como inciertos. La respuesta pidiendo aclaración
no cuenta como una acción solicitada. Reconocer una intención tampoco cuenta.
`fallback_consultado` indica una consulta al servicio habilitado; no afirma que
su modelo haya respondido, por ejemplo si la carga falla o vence el plazo.

Para las cuatro órdenes compuestas solicitadas, la traza esperada es
`rechazo_compuesta`, cero ejecutores, cero acciones y `fallback_consultado=false`.

## Verificación y límites

Las pruebas locales usan el cuerpo real del enrutador extraído mediante AST,
con reloj fijo y efectos externos simulados. No abren Spotify ni crean datos
personales. Las entradas de texto y voz se prueban con transcripción simulada;
la prueba manual con micrófono y la aplicación completa queda pendiente.

La detección es léxica y conservadora, no una comprensión general del español.
Un título sin delimitar que parezca contener varias órdenes puede requerir
comillas. No se han ampliado los permisos del clasificador ni modificado sus
predicciones, los parámetros de Whisper, la voz o el diseño de la interfaz.

Ejecutar las regresiones sin entrenar:

```powershell
.venv\Scripts\python.exe tests\ejecutar_regresion_sin_entrenar.py
```

El ejecutor bloquea los métodos de entrenamiento y omite expresamente la prueba
histórica de reentrenamiento. `tests/` y `eva_inteligencia/experimentos/` siguen
ignorados por Git. Los informes locales quedan únicamente dentro de `tests/`.

Resultados de esta corrección:

- Regresión completa: **324 descubiertas, 323 aprobadas y 1 omitida** (la de
  reentrenamiento), en 108,085 s. Informe: `tests/resultado_compuestas_final.txt`.
- Tras el ajuste final de las trazas de excepciones: **22 pruebas específicas
  aprobadas**, en 2,573 s. Informe: `tests/resultado_compuestas_especificas.txt`.
- Cubiertas las cuatro órdenes compuestas solicitadas, comandos individuales,
  consultas alternativas con el modelo oficial, negación, fecha personal, títulos
  con «y», literales con verbos, seguimiento de aclaraciones, ambas configuraciones
  del fallback, observación independiente, entradas de voz/texto simuladas y
  ausencia de ejecuciones duplicadas. Las trazas se aislaron en 60 interacciones
  concurrentes. Las pruebas anteriores también verifican Tkinter y carga sin
  `experimentos/`.
- Las huellas confirman que modelo oficial, experimentos, Whisper, observador,
  clasificador contextual e índice Git no cambiaron. `git diff --check` sin errores.
- Se conservaron los cambios previos del fallback. En esta etapa se modificaron
  `main.py`, `aclaraciones_comandos.py`, se añadieron `ordenes_compuestas.py`,
  `diagnostico_comandos.py` y este documento. Las pruebas y adaptaciones de sus
  fixtures permanecen locales en `tests/`.

Para la comprobación manual, activar sólo el diagnóstico de comandos y pronunciar
«Eva, dime la hora y abre Spotify»: debe pedir una sola instrucción, sin abrir
Spotify ni dar la hora. Repetir en orden inverso y comprobar también ambos comandos
por separado. No se ha realizado esta prueba manual durante la corrección.
