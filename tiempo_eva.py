from datetime import datetime, timedelta
import re


NUMEROS = {
    "cero": 0,
    "una": 1,
    "uno": 1,
    "dos": 2,
    "tres": 3,
    "cuatro": 4,
    "cinco": 5,
    "seis": 6,
    "siete": 7,
    "ocho": 8,
    "nueve": 9,
    "diez": 10,
    "once": 11,
    "doce": 12,
    "trece": 13,
    "catorce": 14,
    "quince": 15,
    "dieciseis": 16,
    "dieciséis": 16,
    "diecisiete": 17,
    "dieciocho": 18,
    "diecinueve": 19,
    "veinte": 20,
    "veintiuno": 21,
    "veintidos": 22,
    "veintidós": 22,
    "veintitres": 23,
    "veintitrés": 23
}


def convertir_numero(texto):

    texto = texto.lower().strip()

    if texto.isdigit():
        return int(texto)

    return NUMEROS.get(texto)


def interpretar_momento_alarma(texto, ahora=None):
    """Momento local completo, sin ejecutar ni modificar los analizadores heredados.

    Reutiliza el parser temporal conservador. Sólo las horas sin fecha admiten
    próxima ocurrencia; una fecha explícita nunca se desplaza al día siguiente.
    """
    from comandos_voz import preparar_comando, normalizar_intencion
    from eva_inteligencia.parametros import _momento

    ahora = ahora or datetime.now()
    if ahora.tzinfo is not None:
        ahora = ahora.astimezone().replace(tzinfo=None)
    comando = preparar_comando(texto)
    orden = re.fullmatch(
        r'(?:por favor\s+)?(?:(?:pon|poner|crea|crear|programa|programar) '
        r'(?:una )?alarma|alarma|despi[eé]rtame)\b\s*(.*?)(?:\s+por favor)?', comando)
    if not orden or not orden[1]:
        raise ValueError('Indica la fecha y una hora completa para la alarma.')
    temporal = re.sub(r'\bpara (las|la)\b', r'a \1', orden[1])
    # Primero respetar la fecha o duración originales. Las otras alternativas
    # sólo pueden completar una hora sola: dos fechas o texto sobrante fallan.
    candidatos = ((temporal, False), ('hoy ' + temporal, True),
                  ('hoy a las ' + temporal, True))
    for expresion, sin_fecha in candidatos:
        try:
            momento, tramos = _momento(expresion, ahora)
        except (ValueError, OverflowError, OSError):
            continue
        resto = expresion
        for inicio, fin in sorted(tramos, reverse=True):
            resto = resto[:inicio] + ' ' + resto[fin:]
        permitidos = ('', 'para') if sin_fecha else ('', 'para', 'el', 'para el')
        if normalizar_intencion(resto) not in permitidos:
            raise ValueError('No pude interpretar toda la fecha y hora. Repite una sola alarma completa.')
        if sin_fecha and momento <= ahora:
            momento += timedelta(days=1)
        if momento <= ahora:
            raise ValueError('La fecha y hora solicitadas ya pasaron. Indica otra; no la cambiaré de día.')
        if (datetime.fromtimestamp(momento.timestamp()) != momento
                or momento.replace(fold=1).timestamp() != momento.timestamp()):
            raise ValueError('La hora local es ambigua o inexistente por cambio de horario. Indica otra.')
        return momento
    raise ValueError('Indica una fecha y hora inequívocas, con mañana/tarde o formato de 24 horas; '
                     'por ejemplo: mañana a las 18:00. Repite la instrucción completa.')


# ==================================================
# INTERPRETAR UNA HORA
# ==================================================

def interpretar_hora(texto):

    texto = texto.lower().strip()

    # ----------------------------------------------
    # FORMATO 18:30
    # ----------------------------------------------

    coincidencia = re.search(
    r"\b(\d{1,2}):(\d{2})\b",
    texto
)

    if coincidencia:

        hora = int(
            coincidencia.group(1)
        )

        minuto = int(
            coincidencia.group(2)
        )

        if (
            0 <= hora <= 23
            and 0 <= minuto <= 59
        ):

            # Si el usuario indicó mañana,
            # tarde o noche, ajustar a 24 horas
            return ajustar_periodo(
                hora,
                minuto,
                texto
            )

    # ----------------------------------------------
    # OCHO Y MEDIA
    # ----------------------------------------------

    if " y media" in texto:

        hora_texto = texto.split(" y media")[0]
        hora_texto = hora_texto.replace("las ", "").strip()

        hora = convertir_numero(hora_texto)

        if hora is not None:
            minuto = 30
            return ajustar_periodo(hora, minuto, texto)

    # ----------------------------------------------
    # OCHO Y CUARTO
    # ----------------------------------------------

    if " y cuarto" in texto:

        hora_texto = texto.split(" y cuarto")[0]
        hora_texto = hora_texto.replace("las ", "").strip()

        hora = convertir_numero(hora_texto)

        if hora is not None:
            minuto = 15
            return ajustar_periodo(hora, minuto, texto)

    # ----------------------------------------------
    # HORA EXACTA: "LAS OCHO"
    # ----------------------------------------------

    palabras = texto.split()

    for palabra in palabras:

        numero = convertir_numero(palabra)

        if numero is not None and 0 <= numero <= 23:

            hora = numero
            minuto = 0

            return ajustar_periodo(
                hora,
                minuto,
                texto
            )

    return None


# ==================================================
# MAÑANA / TARDE / NOCHE
# ==================================================

def ajustar_periodo(hora, minuto, texto):

    if (
        "de la tarde" in texto
        or "de la noche" in texto
    ):

        if 1 <= hora <= 11:
            hora += 12

    elif "de la mañana" in texto:

        if hora == 12:
            hora = 0

    return hora, minuto


# ==================================================
# INTERPRETAR "EN X MINUTOS"
# ==================================================

def interpretar_en_minutos(texto):

    texto = texto.lower().strip()

    # Permitir "dentro de..." además de "en..."
    texto = texto.replace("dentro de ", "en ")

    # Buscar expresiones como:
    # en 5 minutos
    # en 2 horas
    coincidencia = re.search(
        r"en\s+(\d+)\s+(minuto|minutos|hora|horas)",
        texto
    )

    cantidad = None
    unidad = None

    if coincidencia:

        cantidad = int(coincidencia.group(1))
        unidad = coincidencia.group(2)

    else:

        # Buscar cantidades escritas con palabras:
        # en cinco minutos
        # en una hora
        # en dos horas

        coincidencia = re.search(
            r"en\s+([a-záéíóú]+)\s+"
            r"(minuto|minutos|hora|horas)",
            texto
        )

        if coincidencia:

            numero_texto = coincidencia.group(1)

            cantidad = convertir_numero(
                numero_texto
            )

            unidad = coincidencia.group(2)

    if cantidad is None:
        return None

    # Convertir horas a minutos
    if unidad in ("hora", "horas"):
        cantidad = cantidad * 60

    momento = datetime.now() + timedelta(
        minutes=cantidad
    )

    return momento.hour, momento.minute

# ==================================================
# INTERPRETAR FECHA
# ==================================================

def interpretar_fecha(texto):

    texto = texto.lower()
    ahora = datetime.now()

    # ==================================================
    # HOY
    # ==================================================

    if "hoy" in texto:

        return ahora.strftime("%Y-%m-%d")

    # ==================================================
    # MAÑANA
    # ==================================================

    if "mañana" in texto:

        fecha = ahora + timedelta(days=1)

        return fecha.strftime("%Y-%m-%d")

    # ==================================================
    # DÍAS DE LA SEMANA
    # ==================================================

    dias_semana = {
        "lunes": 0,
        "martes": 1,
        "miércoles": 2,
        "miercoles": 2,
        "jueves": 3,
        "viernes": 4,
        "sábado": 5,
        "sabado": 5,
        "domingo": 6
    }

    for nombre_dia, numero_dia in dias_semana.items():

        if nombre_dia in texto:

            dia_actual = ahora.weekday()

            dias_faltantes = (
                numero_dia - dia_actual
            ) % 7

            # Si menciona el día actual,
            # usamos el próximo de ese día.
            if dias_faltantes == 0:
                dias_faltantes = 7

            fecha = ahora + timedelta(
                days=dias_faltantes
            )

            return fecha.strftime(
                "%Y-%m-%d"
            )

    # ==================================================
    # SIN FECHA ESPECÍFICA
    # ==================================================

    return ahora.strftime("%Y-%m-%d")
