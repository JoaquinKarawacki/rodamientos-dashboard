import re

# Mapa oficial de códigos de warning relevantes a rodamientos.
# Fuente: hoja "Instrucciones" del Excel de Peralta.
# El código viene en el campo 'Original Event' del logbook ROTORsoft,
# siempre entre corchetes al principio del texto:
#   "[58.1] Fault lubrication system [Grease reservoir empty]"  → 58.1
MAPA_CODIGOS_WARNING = {
    "58.2":  "Lub. Sin presion",
    "58.5":  "Lub. Sin presion (aux)",
    "58.1":  "Grasa vacio",
    "50.23": "Ruido Nacelle",
    "50.19": "Sensor acust.",
    "72.99": "Air Gap",
}

# Códigos que aparecen en el logbook pero NO son de rodamientos.
# No necesitan estar listados (cualquier código fuera del mapa se ignora),
# pero los dejamos documentados porque la hoja de instrucciones los excluye
# explícitamente y conviene que quede el por qué a la vista.
#   50.13 → Ruido en Spinner (no vinculado a rodamiento trasero)
#   50.18 → Sensor acustico desactivado (1 solo evento, no relevante)

# Captura el contenido del primer corchete al inicio del texto.
PATRON_CODIGO = re.compile(r"^\s*\[([^\]]+)\]")


def extraer_codigo(descripcion: str) -> str | None:
    """
    Extrae el código de evento del texto del logbook.
    'Ej: [58.1] Fault lubrication system [...]' → '58.1'
    Retorna None si el texto no empieza con un código entre corchetes.
    """
    if not descripcion:
        return None

    coincidencia = PATRON_CODIGO.search(descripcion)
    if not coincidencia:
        return None

    return coincidencia.group(1).strip()


def clasificar_warning(descripcion: str) -> str | None:
    """
    Recibe el texto del campo 'Original Event' del logbook ROTORsoft.
    Retorna el tipo de warning de rodamiento si su código está en el
    mapa oficial, o None si el evento no es relevante a rodamientos.
    """
    codigo = extraer_codigo(descripcion)
    if codigo is None:
        return None

    return MAPA_CODIGOS_WARNING.get(codigo)

