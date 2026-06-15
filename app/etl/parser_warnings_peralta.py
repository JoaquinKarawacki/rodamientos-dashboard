import re
from app.etl.parser_rodamientos import _cargar_filas, _normalizar, _encontrar_header

# Mapeo de abreviatura de mes en español (como aparece en los encabezados
# tipo "Ene'25") al numero de mes.
MESES = {
    "ene": 1, "feb": 2, "mar": 3, "abr": 4,  "may": 5,  "jun": 6,
    "jul": 7, "ago": 8, "sep": 9, "oct": 10, "nov": 11, "dic": 12,
}

# Los seis tipos oficiales, tal como aparecen como encabezados de columna
# en la hoja Warnings_por_Tipo. Tienen que matchear con los nombres que
# devuelve el clasificador para que el dashboard los una bien.
TIPOS_OFICIALES = [
    "Lub. Sin presion",
    "Lub. Sin presion (aux)",
    "Grasa vacio",
    "Ruido Nacelle",
    "Sensor acust.",
    "Air Gap",
]


def _parsear_encabezado_mes(texto: str) -> tuple[int, int] | None:
    """
    Convierte un encabezado tipo "Ene'25" en (mes, anio).
    "Ene'25" -> (1, 2025);  "Dic'26" -> (12, 2026)
    Devuelve None si el texto no es un encabezado de mes valido.
    """
    texto = _normalizar(texto).lower()
    match = re.match(r"([a-z]{3})'?(\d{2})", texto)
    if not match:
        return None

    abrev, anio_corto = match.group(1), match.group(2)
    if abrev not in MESES:
        return None

    return MESES[abrev], 2000 + int(anio_corto)


def parsear_warnings_mensuales(ruta_archivo: str) -> list[dict]:
    """
    Lee la hoja Warnings_Mensuales (meses en columnas) y devuelve una
    fila por cada combinacion turbina+mes con cantidad > 0.
    """
    filas = _cargar_filas(ruta_archivo, "Warnings_Mensuales")
    idx = _encontrar_header(filas, "WEC")
    encabezados = [_normalizar(c) for c in filas[idx]]

    # Detectar que columnas son meses y a que (mes, anio) corresponden.
    columnas_mes = {}
    for i, enc in enumerate(encabezados):
        periodo = _parsear_encabezado_mes(enc)
        if periodo:
            columnas_mes[i] = periodo

    col_wec = encabezados.index("WEC")

    registros = []
    for fila in filas[idx + 1:]:
        codigo = _normalizar(fila[col_wec])
        if not codigo.upper().startswith("PSP"):
            continue

        for i, (mes, anio) in columnas_mes.items():
            valor = fila[i]
            if valor is None:
                continue
            try:
                cantidad = int(valor)
            except (TypeError, ValueError):
                continue
            if cantidad <= 0:
                continue  # no guardamos meses sin warnings

            registros.append({
                "codigo_turbina": codigo,
                "mes":            mes,
                "anio":           anio,
                "cantidad":       cantidad,
            })

    return registros


def parsear_warnings_por_tipo(ruta_archivo: str) -> list[dict]:
    """
    Lee la hoja Warnings_por_Tipo (tipos en columnas) y devuelve una
    fila por cada combinacion turbina+tipo con cantidad > 0.
    El dato es acumulado de todo el periodo: mes y anio van en null.
    """
    filas = _cargar_filas(ruta_archivo, "Warnings_por_Tipo")
    idx = _encontrar_header(filas, "WEC")
    encabezados = [_normalizar(c) for c in filas[idx]]

    # Mapear cada tipo oficial a su indice de columna. Comparamos
    # normalizando tildes/espacios para tolerar "Lub. Sin presión"
    # (con tilde, como viene en el Excel) vs "Lub. Sin presion".
    def sin_tildes(t):
        reemplazos = (("á","a"),("é","e"),("í","i"),("ó","o"),("ú","u"))
        t = t.lower()
        for a, b in reemplazos:
            t = t.replace(a, b)
        return t

    columnas_tipo = {}
    for tipo_oficial in TIPOS_OFICIALES:
        objetivo = sin_tildes(tipo_oficial)
        for i, enc in enumerate(encabezados):
            if sin_tildes(enc) == objetivo:
                columnas_tipo[tipo_oficial] = i
                break

    col_wec = encabezados.index("WEC")

    registros = []
    for fila in filas[idx + 1:]:
        codigo = _normalizar(fila[col_wec])
        if not codigo.upper().startswith("PSP"):
            continue

        for tipo_oficial, i in columnas_tipo.items():
            valor = fila[i]
            if valor is None:
                continue
            try:
                cantidad = int(valor)
            except (TypeError, ValueError):
                continue
            if cantidad <= 0:
                continue

            registros.append({
                "codigo_turbina": codigo,
                "tipo":           tipo_oficial,
                "mes":            None,   # acumulado historico: sin mes
                "anio":           None,
                "cantidad":       cantidad,
            })

    return registros