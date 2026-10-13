"""
Carga el nombre visible (marca + nro de serie del rodamiento) de cada
aerogenerador de Peralta (PSP) en la columna `etiqueta` de la turbina.

Fuente: Excel "Rodamientos_Hub_Resumen (1).xlsx" (raiz del proyecto),
hoja "Rodamientos - Detalle":
  - columna "Aerogenerador"                     -> numero de turbina (1..50)
  - columna "Nombre para agregar a cada WEC"    -> texto a mostrar ("1 - PSL 2823")

El codigo interno (PSP-01) NO se toca: es la clave de cruce del ETL.
Idempotente: se puede volver a correr; solo reescribe `etiqueta`.

Uso:
    python scripts/cargar_etiquetas_peralta.py
    python scripts/cargar_etiquetas_peralta.py "ruta/al/Excel.xlsx"
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import FabricaSesion
from app.etl.parser_rodamientos import _cargar_filas, _normalizar, _encontrar_header
from app.repositorios.repositorio_parque import RepositorioParque
from app.repositorios.repositorio_turbina import RepositorioTurbina

RUTA_DEFAULT = "Rodamientos_Hub_Resumen (1).xlsx"
HOJA         = "Rodamientos - Detalle"
COL_NUMERO   = "Aerogenerador"
COL_NOMBRE   = "Nombre para agregar a cada WEC"


def leer_etiquetas(ruta: str) -> dict[int, str]:
    """Devuelve {numero_turbina: nombre_visible} desde el Excel."""
    filas  = _cargar_filas(ruta, HOJA)
    header = _encontrar_header(filas, COL_NUMERO)
    col    = {_normalizar(v): i for i, v in enumerate(filas[header]) if v is not None}

    if COL_NUMERO not in col or COL_NOMBRE not in col:
        raise ValueError(
            f"Faltan columnas. Esperadas '{COL_NUMERO}' y '{COL_NOMBRE}'. "
            f"Encontradas: {list(col.keys())}"
        )

    etiquetas: dict[int, str] = {}
    for fila in filas[header + 1:]:
        numero = fila[col[COL_NUMERO]]
        nombre = fila[col[COL_NOMBRE]]
        if numero is None or nombre is None or str(nombre).strip() == "":
            continue
        etiquetas[int(numero)] = str(nombre).strip()
    return etiquetas


def main() -> None:
    ruta = sys.argv[1] if len(sys.argv) > 1 else RUTA_DEFAULT
    if not os.path.exists(ruta):
        print(f"[ERROR] No existe el Excel: {ruta}")
        sys.exit(1)

    etiquetas = leer_etiquetas(ruta)
    print(f"Leidas {len(etiquetas)} etiquetas del Excel.")

    sesion = FabricaSesion()
    try:
        parque = RepositorioParque(sesion).obtener_por_codigo("PSP")
        if not parque:
            print("[ERROR] Parque 'PSP' no encontrado. Corriste seed.py?")
            sys.exit(1)

        turbinas = RepositorioTurbina(sesion).obtener_todos(parque.id)
        actualizadas = 0
        sin_match    = []
        for t in turbinas:
            nombre = etiquetas.get(t.numero)
            if nombre:
                t.etiqueta = nombre
                actualizadas += 1
            else:
                sin_match.append(t.codigo)

        sesion.commit()
        print(f"OK: {actualizadas}/{len(turbinas)} turbinas de Peralta actualizadas.")
        if sin_match:
            print(f"Sin etiqueta en el Excel (quedan con su codigo): {sin_match}")
    except Exception as error:
        sesion.rollback()
        print(f"[ERROR] {error}")
        sys.exit(1)
    finally:
        sesion.close()


if __name__ == "__main__":
    main()
