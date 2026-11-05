# Diagnóstico de voz y recuperación de regresiones

Se conserva el clasificador de caracteres `v03_01`, con sus mismos umbrales. No se
modificó `main.py`, no se habilitaron funciones ejecutoras ni se cambiaron Whisper Small,
sus parámetros, Spotify, Gemini, alarmas, recordatorios o pyttsx3.

## Cómo probar con el micrófono real

En una terminal situada en la raíz del proyecto:

```powershell
.venv\Scripts\python.exe -m eva_inteligencia.diagnostico_whisper --microfono
```

1. Espera a que termine la carga de Small desde la caché local. Se carga una sola vez.
2. Pulsa **Enter** para capturar una frase. El micrófono no escucha entre intentos.
3. Guarda silencio durante el segundo de calibración. Habla cuando aparezca **«Habla ahora»**.
4. Termina la frase y haz una pausa. El micrófono se cierra antes de la transcripción.
5. Revisa el JSON: `transcripcion`, `intencion_candidata`, `parametros`, `estado` y `motivo`.
   El estado será `aceptada`, `aclaracion` o `desconocida`; un fallo se comunica como error.
   **Aceptada significa propuesta válida para diagnóstico, nunca acción ejecutada.**
6. Pulsa Enter para otro intento, o escribe **q** y Enter para salir. **Ctrl+C** cancela.

Si el dispositivo predeterminado no es el correcto:

```powershell
.venv\Scripts\python.exe -m eva_inteligencia.diagnostico_whisper --listar-microfonos
.venv\Scripts\python.exe -m eva_inteligencia.diagnostico_whisper --microfono --dispositivo 2
```

Sustituye `2` por el índice de tu entrada de micrófono. La enumeración puede incluir
salidas de audio o interfaces duplicadas; elige el dispositivo de entrada correspondiente.
Si no abre, comprueba la selección, los permisos de micrófono de Windows y si otra
aplicación ocupa el dispositivo. No hace falta iniciar EVA ni abrir aplicaciones para probar.

El diagnóstico usa el modelo anterior por defecto; `--modelo` permite elegir explícitamente
un artefacto local de confianza. No se descargan modelos ni se usa un fallback de red.
Si Small no está disponible en caché, el diagnóstico informa el fallo antes de abrir el micrófono.

## Guion manual sugerido

Estas frases son sintéticas; no hace falta dictar información personal:

| Frase que puedes decir | Qué comprobar |
|---|---|
| Dime la hora | Transcripción correcta; propuesta de consultar hora, sin ejecutarla |
| Informa la hora que tienes en pantalla | Recuperación del contexto de reloj local |
| Me lees lo que tengo pendiente de recordar | Consulta de recordatorios; no se leen datos reales |
| Para la alarma | Intención de detener alarma; no se detiene ninguna |
| Cierra la calculadora | Objeto autorizado; la aplicación permanece sin cambios |
| No cierres la calculadora | Aclaración por negación; ninguna propuesta aceptada |
| Abre Paint y pausa la música | Diagnóstico de varias solicitudes; ninguna se acepta parcialmente |
| Pon música igual que ayer | Aclaración: no existe historial musical para resolverlo |
| Cuál es la fecha de mi examen | Desconocida: no equivale a la fecha actual |
| Necesito ayuda con geometría | Sin propuesta local |

Whisper puede escribir «cierra» correctamente aunque se escuche un homófono. Para probar
de forma determinista el texto «Sierra la calculadora», usa el modo de transcripciones:

```powershell
.venv\Scripts\python.exe -m eva_inteligencia.diagnostico_whisper
```

Escribe o pega una frase por línea. «Sierra la calculadora» debe pedir que se repita la orden;
no se cambia automáticamente «sierra» por «cierra». Ctrl+Z y Enter termina la entrada en Windows.
También se conserva `--wav "C:\ruta\grabacion.wav"` para un audio elegido explícitamente.

## Privacidad y reutilización

La captura requiere `--microfono` y Enter para cada frase; no hay grabación de fondo.
Audio y transcripción sólo viven en memoria y se muestran en consola. No se escriben archivos,
historiales, asociaciones personales ni datos de entrenamiento. No hay opción de exportar
transcripciones: `--salida-metricas` sólo admite la medición conjunta ya existente.
Una redirección de consola decidida por el usuario sí puede guardar su salida.

Se reutiliza `whisper_control.configurar_captura`: mismo umbral de pausa y demás configuración
de EVA, calibración de un segundo y escucha sin recortar la frase con un límite nuevo.
Se convierte el audio en memoria a WAV de 16 kHz y 16 bits, como `ControlWhisper.transcribir`.
La transcripción llama directamente a `_transcribir_wav`, con todos sus parámetros intactos.
No se importa `main.py` ni se conecta el resultado a comandos, TTS o servicios.

## Correcciones acotadas

| Regresión o ambigüedad | Resultado de esta etapa |
|---|---|
| «EVA informa la hora que tienes en pantalla» | Recuperada como consultar hora; se permite la referencia local a pantalla |
| «Me lees lo que tengo pendiente de recordar» | Recuperada mediante un patrón acotado de consulta singular |
| «Eba para la al arma» | Recuperada sólo dentro de una petición completa e inequívoca de detener alarma; no se sustituye «al arma» globalmente |
| «Sierra la calculadora» | Pide aclaración y repetición; no se autocorrige ni se acepta |
| «Pon música igual que ayer» | Pide canción concreta o continuar; no inventa un título a partir del historial ausente |

Las variantes negativas/compuestas pasan primero por las protecciones existentes. Se probaron
contrastes como «Sierra Nevada», «Sierra la madera con cuidado», «al arma de fuego», fechas
personales, consultas ajenas a recordatorios y negaciones. Un título explícito como
«Reproduce la canción Igual que ayer» no se reescribe como una referencia histórica.

## Comparación sobre los mismos conjuntos

Se archivaron los módulos anteriores antes de editarlos. `evaluar_voz.py` reproduce exactamente
las salidas de la etapa contextual y después evalúa los cambios con el mismo modelo y reloj
de prueba. Los archivos históricos no se sobrescriben. Estos conjuntos ya son conocidos:
**son regresión, no una evaluación ciega nueva ni una medición de voz real**.

| Conjunto | Cobertura conocidas antes → después | Precisión de propuestas antes → después | Rechazo desconocidas antes → después |
|---|---:|---:|---:|
| Desafío v04: 33 completas y 42 desconocidas | 45,5 % → 54,5 % (15 → 18) | 100 % → 100 % | 100 % → 100 % |
| Contexto natural: 22 completas y 12 desconocidas | 63,6 % → 63,6 % | 100 % → 100 % | 100 % → 100 % |
| Contexto adversarial: 8 completas y 24 desconocidas | 75 % → 75 % | 100 % → 100 % | 100 % → 100 % |

En las ocho peticiones incompletas/ambiguas del adversarial, las propuestas indebidas pasan
de **1 a 0**. Los otros conjuntos mantienen cero. No aumentaron propuestas erróneas ni se
redujo cobertura o rechazo en los conjuntos comparados, por lo que se conservan los cambios.
Esto no garantiza ausencia de errores futuros: los casos son sintéticos y las muestras pequeñas.

Datos completos, diferencias por frase, métricas por intención y hashes en
`experimentos/voz_v01/informe.json` y `congelacion.json`. No se ajustó ni reentrenó el modelo.
La reserva de 58 frases permanece intacta y no se usó para ajustar estas reglas.

## Pruebas y pendientes

**214 pruebas aprobadas: 196 anteriores y 18 nuevas**, en 70,59 segundos, salida 0.
Registro: `tests/resultado_voz_regresion_final.txt`. Las pruebas nuevas cubren recuperaciones,
contrastes ambiguos, negaciones, compuestas, transcripción/estado/motivo, captura en memoria,
cierre al cancelar, Enter por intento, una única carga de Small, error de permisos, falta del
modelo, enumeración sin captura y ausencia de exportación de transcripciones.

Las pruebas del micrófono utilizan dobles, no voz humana. La comprobación de hardware pudo
enumerar 21 dispositivos de audio en Windows **sin abrir un flujo de captura**. Esto confirma
enumeración y dependencias, no calidad de la captura ni del reconocimiento.

La sesión real con voz humana sigue pendiente de ejecución y revisión del usuario. No se
afirma haber validado acentos, ruido, calidad del micrófono o transcripciones reales de esta
etapa. Tampoco se puede recuperar con certeza una negación que Whisper omita. «Sierra» se
mantiene intencionadamente sin aceptación automática. Las demás limitaciones del analizador
contextual finito siguen aplicándose.

## Archivos

- Modificados: `contexto.py` y `diagnostico_whisper.py`.
- Nuevo: `evaluar_voz.py`, este documento y los artefactos de `experimentos/voz_v01/`.
- Pruebas: nuevo `tests/test_diagnostico_microfono.py`; ajuste de `test_contexto_local.py`
  para verificar los hashes históricos de los módulos editados contra sus copias archivadas,
  conservando intactos los demás controles. El informe nuevo verifica además los hashes actuales.

`tests/` sigue ignorado; no se hicieron git add, commit, push ni merge. No se modificaron
datos personales, configuración privada, archivos `.cache`, `main.py` ni componentes ejecutores.
La rama comprobada es `inteligencia-local-eva`.
