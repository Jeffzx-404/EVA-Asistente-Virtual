# Correcciones del enrutador tradicional

Trabajo en `inteligencia-local-eva`. Se conserva la integración previa en modo
observación y sus cambios sin commit. No se ha modificado la rama `main`.

## Causas y comparación reproducida

Los cinco casos se ejecutaron con el procesador extraído de `main.py`, reloj
fijo y funciones simuladas para abrir aplicaciones, guardar recordatorios,
responder con voz, consultar Gemini y controlar Spotify. La comparación anterior
usa una copia del código tomada antes de esta etapa, dentro de `tests/`.

| Entrada | Causa confirmada | Resultado corregido |
|---|---|---|
| «Eva, dime qué hora es» | `es_consulta_hora` admitía «qué hora es» y «dime la hora», pero no su combinación; acababa en Gemini. | Lee `datetime.now()` del equipo; no consulta Gemini. Con el reloj simulado respondió 11:20. |
| «Eva, abre la calculadora» | No se encontró discrepancia. | Se conserva una sola llamada al ejecutor tradicional. |
| «Eva, recuérdame estudiar mañana a las seis» | El analizador tradicional devolvía `(6, 0)` sin verificar el período. | Pide mañana/tarde; no guarda hasta completar la información. |
| «Eva, qué fecha es mi examen» | La condición de fecha buscaba la subcadena «qué fecha es» dentro de cualquier frase. | Informa que no conoce la fecha del evento personal, sin sustituirla por hoy ni consultar Gemini. |
| «Eva, pon música igual que ayer» | El enrutador pasaba el resto de la petición al buscador de Spotify sin comprobar referencias al historial. | Pide un título concreto o continuar; no consulta Spotify para adivinarlo. |

Se confirmó el envío incorrecto del primer caso a Gemini, pero no se invocó ese
servicio para reproducir la frase exacta «No tengo acceso a la hora en tiempo real».
En música se confirmó la consulta literal incorrecta; no se probó qué canción
elegiría el catálogo real de Spotify. La respuesta incorrecta de fecha personal
sí se reprodujo directamente con el reloj simulado.

## Validación y aclaraciones

`aclaraciones_comandos.py` reutiliza funciones puras de `contexto.py` y
`parametros.py`. No importa el clasificador, sklearn ni ejecutores. La decisión
de atender un comando sigue perteneciendo al enrutador tradicional.

Para los recordatorios con hora fija se exige descripción, fecha y hora completas.
«Mañana a las seis» no especifica AM/PM: *mañana* indica el día siguiente.
«Mañana a las seis de la tarde» y «mañana a las 18:00» sí son inequívocas.
El formato `06:00` se interpreta como hora explícita de 24 horas, igual que en
el extractor existente. Si falta la fecha, se pide «hoy», «mañana» o una fecha
concreta; ya no se asigna hoy silenciosamente. Se conserva la ruta tradicional
de duraciones relativas como «en una hora» y el comportamiento de las alarmas.

Cuando el extractor puede obtener alternativas válidas para el período horario,
EVA acepta una respuesta como «de la mañana», «de la tarde», «PM» o una hora
completa que coincida con una de esas alternativas, por ejemplo «18:00». Las opciones
guardan la fecha concreta del primer mensaje: responder tras medianoche no mueve
el recordatorio otro día. Antes de guardar se comprueba que la hora siga en el
futuro. Para otros datos faltantes se solicita repetir el recordatorio completo.

Para música contextual, se acepta después «la canción Despacito» o una petición
completa como «reproduce la canción Igual que ayer». Ese título explícito sigue
siendo válido. «Continúa la música» conserva su función tradicional. No se
interpreta automáticamente una respuesta libre como un título ni se inventa un
historial musical.

El seguimiento tiene estas reglas:

- Una sola solicitud pendiente por sesión, compartida entre texto y voz, con
  caducidad de 120 segundos medida con reloj monotónico.
- Sólo memoria: no se escriben solicitudes ni conversaciones en preferencias
  ni en otros archivos. Al reiniciar no hay una aclaración pendiente.
- «Cancelar» o «no» cancela. Un comando independiente sustituye el contexto
  pendiente. Una respuesta insuficiente requiere repetir la instrucción completa.
- La respuesta se consume bajo bloqueo antes de ejecutar. Dos respuestas
  concurrentes no crean dos recordatorios. Un número de turno impide que una
  solicitud antigua sobrescriba una más reciente.
- Los bloqueos no abarcan voz, Tkinter, Spotify ni persistencia. Un fallo de
  almacenamiento no anuncia éxito ni provoca reintentos automáticos; debe
  repetirse la instrucción completa tras resolverlo.
- Las respuestas de aclaración con alternativas o instrucciones añadidas no
  seleccionan silenciosamente una parte para ejecutarla.

El observador continúa recibiendo únicamente las entradas originales. No recibe
parámetros completados, no consume aclaraciones y no crea acciones. Por eso el
diagnóstico independiente de «de la tarde» puede indicar desconocido aunque el
enrutador tradicional complete una solicitud pendiente. Esa diferencia es
esperada: el observador no comparte el estado del seguimiento.

## Archivos de esta etapa

- `comandos_voz.py`: variante de hora y coincidencia completa para fecha actual.
- `aclaraciones_comandos.py` (nuevo): validación pura y seguimiento temporal seguro.
- `main.py`: conexión del seguimiento y validaciones; dos funciones pequeñas
  comparten los ejecutores ya existentes de recordatorios y búsqueda musical.
- `CORRECCIONES_COMANDOS.md` (nuevo): este informe.
- Sólo en `tests/`: nuevas pruebas y reproducción antes/después; actualización de
  las fixtures de comandos y de observación, y una entrada de la prueba de fallo
  de persistencia para que contenga fecha y hora válidas.

No se modificaron `tiempo_eva.py`, los módulos de Spotify/Gemini, la interfaz,
Whisper, pyttsx3, persistencia, el clasificador, sus umbrales ni el observador.
Los archivos previos de `eva_inteligencia/experimentos/` no se alteraron.

## Alcance de las verificaciones

Resultado final: **264 pruebas aprobadas en 37,923 segundos**: las 235 pruebas
anteriores, con sus fixtures adaptadas al seguimiento y a horarios explícitos,
y 29 pruebas nuevas. `git diff --check` terminó sin incidencias.

Las pruebas nuevas abarcan los cinco casos, variantes de fecha/hora, errores de
transcripción ya admitidos, horas inválidas, campos ausentes, títulos explícitos,
caducidad, cambio de día, cancelación, respuestas compuestas, concurrencia y
fallos de persistencia/observador. Un proceso limpio verifica que la validación
tradicional no carga el modelo ni servicios. Se comprueba también que las
conexiones de texto/voz y el cuerpo de captura y síntesis no cambiaron.

Los resultados se conservan sólo como pruebas sintéticas locales en
`tests/discrepancias_antes.json`, `tests/discrepancias_despues.json` y
`tests/resultado_discrepancias_regresion.txt`. `tests/` permanece ignorado por Git.

Falta repetir los casos manualmente en la aplicación completa con micrófono,
ventana visible y servicios configurados. No se capturó audio ni se ejecutaron
Spotify o recordatorios personales para estas comprobaciones. La validación
determinista cubre las formas comprobadas; no demuestra comprensión de cualquier
paráfrasis. No se amplió esta etapa a reescribir las demás rutas tradicionales.
