# Cierre explícito de EVA y fecha de alarmas

**Actualización posterior:** el defecto de fecha documentado abajo se corrigió
en la etapa [Alarmas con fecha completa](ALARMAS_FECHA_COMPLETA.md). Este informe
conserva la reproducción y los resultados históricos de la revisión de cierre.

Trabajo sobre `inteligencia-local-eva`, conservando íntegramente los cambios
pendientes de la auditoría sobre `d9da305`.

## Causa y corrección de cierre

`comandos_voz.preparar_comando` elimina el vocativo inicial y también una EVA
final. Por ello `Eva, cierra EVA` se convierte en `cierra`. `main.py` conserva
la entrada en `pregunta_original`, pero la excepción anterior sólo recuperaba
el destino para el infinitivo `cerrar`. El imperativo `cierra` terminaba en
Gemini. Se reprodujo esa ruta con la versión anterior y ejecutores simulados.

La corrección se limita a la condición de cierre de `main.py`:

- Reconoce `cierra EVA` y `cerrar EVA`.
- Si el normalizador retiró el destino, exige que la entrada original completa
  sea una orden de cierre dirigida a EVA, con vocativo inicial opcional.
- No acepta `cierra` ni `cerrar` solos, preguntas, negaciones o coincidencias
  parciales. La protección de órdenes compuestas sigue actuando antes.
- Devuelve la señal `False` ya existente. Los adaptadores de texto/voz y la
  cola de Tkinter realizan el cierre sin modificaciones.

No se cambia el normalizador compartido para no alterar otras intenciones ni
predicciones. Por tanto, el campo diagnóstico `texto_normalizado` puede seguir
mostrando `cierra`; ahora la decisión de cierre comprueba también el destino
explícito en la entrada original y no pasa a Gemini.

## Alarmas: defecto confirmado, no corregido en esta verificación

La ruta tradicional extrae únicamente `(hora, minuto)` y llama a
`crear_alarma(hora, minuto, funcion_aviso)`. No transmite la fecha solicitada.
El ejecutor calcula la próxima ocurrencia de esa hora a partir del reloj local.
El vencimiento se conserva en la memoria del vigilante, no en un archivo de
alarmas. El mensaje de confirmación no permite comprobar la fecha.

Resultados con reloj simulado (fechas fijas de prueba):

| Reloj al crear | Petición | Vencimiento real calculado |
|---|---|---|
| 11/11/2026 07:00 | hoy a las 08:00 | 11/11/2026 08:00 |
| 11/11/2026 07:00 | mañana a las 08:00 | **11/11/2026 08:00: incorrecto** |
| 11/11/2026 09:00 | hoy a las 08:00 | **12/11/2026 08:00: cambia el día solicitado** |
| 11/11/2026 09:00 | mañana a las 08:00 | 12/11/2026 08:00, por ser la siguiente ocurrencia |

Se ejecutó el vigilante con reloj simulado en el primer vencimiento incorrecto:
emitió un aviso y llamó una vez al sonido simulado el mismo día. No se reprodujo
sonido real ni se crearon hilos de alarma reales. **Hoy y mañana no se distinguen
correctamente.** La aprobación de estas pruebas caracteriza el defecto; no
significa que las alarmas con fecha estén corregidas.

Se conserva `alarmas.py` exactamente como estaba al comenzar esta revisión,
conforme al alcance solicitado de investigar/documentar inicialmente su fecha.
Corregir el defecto requiere transmitir una fecha validada desde el enrutador
al ejecutor y comprobar su confirmación, sin confundir el día con «de la
mañana». No se añadió ese cambio ni persistencia de alarmas en esta etapa.
No se inspeccionaron alarmas personales, por lo que no se afirma la fecha de la
alarma particular creada durante la prueba manual del usuario.

## Pruebas y archivos

`tests/test_cierre_destino.py`: diez pruebas nuevas. Siete cubren reproducción
del fallo anterior, cierre por texto/transcripción simulada, negaciones,
preguntas, destino Spotify, orden incompleta, composición, Tkinter oculto y
conservación de archivos. Tres caracterizan la fecha de alarmas.

Las diez aprobaron en 1,331 segundos. Regresión final completa: **430 pruebas
descubiertas, 429 aprobadas y una omitida por requerir reentrenamiento**, en
**106,396 segundos**, con código de salida 0. No hubo errores ni avisos de
limpieza de Tkinter en esta ejecución final.

La primera pasada completa también terminó con 429 aprobadas y una omitida,
pero emitió un aviso de recolección de una imagen de Tkinter fuera de su hilo.
Se corrigió la liberación de la vista en la nueva prueba, sin cambiar la
interfaz de EVA, y se repitió la suite. `git diff --check` no informó errores;
las carpetas `tests/` y `experimentos/` siguen fuera del índice Git.

Evidencias locales ignoradas:

- `tests/resultado_cierre_destino_antes.txt`
- `tests/resultado_cierre_destino_despues.txt`
- `tests/resultado_cierre_destino_regresion.txt`
- `tests/resultado_cierre_destino_final.txt`
- `tests/fixtures/cierre_destino/`: copia previa y huellas de integridad.

Archivos de esta revisión: `main.py`, este informe y pruebas/evidencias locales.
La prueba de integridad verifica que el normalizador, la interfaz, los
trabajadores, alarmas, recordatorios, persistencia, preferencias, Whisper,
el modelo oficial y el índice Git no cambiaron respecto al inicio de esta
revisión. Las demás funciones de `main.py` conservan su AST anterior.

## Validación manual pendiente

- Repetir `Eva, cierra EVA` por texto y micrófono real: despedida única, cierre
  de ventana y ausencia de consulta a Gemini.
- Comprobar que `Eva, cierra` y la orden compuesta no cierran ni abren aplicaciones.
- No dar por válida una alarma para un día explícito basándose sólo en la
  respuesta de EVA. Su fecha requiere la corrección pendiente descrita arriba.
- Micrófono, audio, notificaciones reales y desaparición de procesos requieren
  pruebas manuales; no se certifican a partir de estas simulaciones.

No se entrenaron modelos, no se cambiaron opciones experimentales ni datos
personales, y no se ejecutaron operaciones de publicación en Git.
