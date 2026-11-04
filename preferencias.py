"""Preferencias validadas y actualizaciones parciales bajo un único bloqueo."""

from persistencia import AlmacenJSON, ErrorPersistencia, avisar


def preferencias_iniciales():
    return {"nombre_usuario": "", "musica_favorita": "", "aplicacion_favorita": ""}


def validar_preferencias(datos):
    resultado = preferencias_iniciales()
    if not isinstance(datos, dict):
        return resultado, False
    # Preservar campos desconocidos para no borrar extensiones anteriores.
    resultado.update(datos)
    valido = True
    for campo in preferencias_iniciales():
        if not isinstance(resultado[campo], str):
            resultado[campo] = ""
            valido = False
    return resultado, valido


_almacen = AlmacenJSON("preferencias.json", validar_preferencias,
                       preferencias_iniciales, reparar=True)


def cargar_preferencias():
    try:
        with _almacen.transaccion() as ruta:
            return _almacen.leer(ruta)
    except ErrorPersistencia as error:
        avisar(str(error))
        return preferencias_iniciales()


def guardar_preferencias(cambios, solo_si_vacios=False):
    """Recibir sólo los campos cambiados, sin sobrescribir una lectura antigua."""
    try:
        if not isinstance(cambios, dict) or not validar_preferencias(cambios)[1]:
            raise ErrorPersistencia("No se guardaron las preferencias: datos incorrectos.")
        with _almacen.transaccion() as ruta:
            actuales = _almacen.leer(ruta)
            if solo_si_vacios:
                # El arranque no debe reemplazar una preferencia recién guardada
                # por otra instancia de EVA después de nuestra primera lectura.
                cambios = {k: v for k, v in cambios.items() if not actuales.get(k)}
            actuales.update(cambios)
            _almacen.guardar(ruta, actuales)
            return actuales
    except ErrorPersistencia as error:
        avisar(str(error))
        return None
