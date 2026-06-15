import pandas as pd
from datetime import datetime, timedelta
from app.etl.clasificador_warnings import clasificar_warning, extraer_codigo
from app.etl.parser_rodamientos import _normalizar

# ROTORsoft guarda las fechas como numeros seriales de Excel.
# El origen es el 30/12/1899 (por el bug historico de Excel que conto
# 1900 como bisiesto). Ej: 46023.0 = 1 de enero 2026 00:00.
ORIGEN_EXCEL = datetime(1899, 12, 30)


def _a_datetime(valor):
    """
    Convierte el valor de la columna Start a datetime. ROTORsoft a veces
    trae seriales de Excel (float) y a veces pandas ya los parsea a
    Timestamp/datetime. Manejamos ambos casos.
    """
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return None
    # pandas ya lo parseo como fecha
    if isinstance(valor, datetime):
        return valor
    if hasattr(valor, "to_pydatetime"):  # pandas Timestamp
        return valor.to_pydatetime()
    # serial numerico de Excel
    try:
        return ORIGEN_EXCEL + timedelta(days=float(valor))
    except (TypeError, ValueError):
        return None

def _extraer_codigo_turbina(planta, codigo_parque: str) -> str | None:
    """
    Extrae el codigo de turbina del campo 'Plant' del logbook.
    Cada parque trae un formato distinto:
      Cerro Grande: 'E921084-CG10'   -> el codigo va al final como -CGxx
      Peralta:      'PSP-48 E920311' -> el codigo va al principio como PSP-xx
    En ambos casos lo traducimos al codigo interno de la DB (WECxx / PSP-xx).
    """
    if planta is None or (isinstance(planta, float) and pd.isna(planta)):
        return None

    planta = str(planta).strip()

    if codigo_parque == "CG":
        import re
        match = re.search(r"-CG(\d+)$", planta)
        if match:
            return f"WEC{int(match.group(1)):02d}"

    if codigo_parque == "PSP":
        import re
        # El codigo PSP-xx esta al principio, antes del espacio.
        match = re.match(r"(PSP-\d+)", planta)
        if match:
            return match.group(1)

    return None


def parsear_logbook(ruta_archivo: str, codigo_parque: str) -> list[dict]:
    """
    Lee el logbook ROTORsoft y devuelve SOLO los eventos clasificados
    como warnings de rodamiento. No agrega ni cuenta: eso es trabajo
    del agregador. Cada elemento es un evento individual ya clasificado.

    El Excel tiene 1 fila de titulo antes de los encabezados:
      Fila 0: "ROTORsoft-Logbook Cerro Grande (...)"
      Fila 1: encabezados   <- skiprows=1
      Fila 2+: eventos
    """
    df = pd.read_excel(ruta_archivo, sheet_name="Sheet0", skiprows=1)
    df.columns = [_normalizar(c) for c in df.columns]

    eventos = []

    for _, fila in df.iterrows():
        # Solo nos interesan los eventos categoria 'warning'
        if str(fila.get("Event Category", "")).strip() != "warning":
            continue

        codigo_turbina = _extraer_codigo_turbina(fila.get("Plant"), codigo_parque)
        if not codigo_turbina:
            continue  # estacion meteorologica u otro dispositivo, no turbina

        descripcion = str(fila.get("Original Event", ""))
        tipo_warning = clasificar_warning(descripcion)
        if not tipo_warning:
            continue  # warning que no es de rodamientos -> se descarta

        fecha_inicio = _a_datetime(fila.get("Start (Brasilia Time)"))
        if fecha_inicio is None:
            continue

        eventos.append({
            "codigo_turbina": codigo_turbina,
            "fecha_inicio":   fecha_inicio,
            "mes":            fecha_inicio.month,
            "anio":           fecha_inicio.year,
            "tipo_warning":   tipo_warning,
        })

    return eventos
