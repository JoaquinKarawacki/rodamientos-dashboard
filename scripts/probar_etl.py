import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import FabricaSesion
from app.servicios.servicio_carga import ServicioCarga

CARPETA = os.path.dirname(__file__)

# Rodamientos (Estado_Rodamientos + Nuevo_Control en el mismo archivo)
RUTA_RODAMIENTOS_CG  = os.path.join(CARPETA, "Cerro_Grande_Actualizacion_Rodamientos.xlsx")
RUTA_RODAMIENTOS_PSP = os.path.join(CARPETA, "Peralta_Actualizacion_Rodamientos .xlsx")

# Seed historico de Peralta (hojas Warnings_Mensuales + Warnings_por_Tipo)
RUTA_SEED_WARNINGS_PSP = os.path.join(CARPETA, "seed_rodamientos_psp.xlsx")

# Logbooks ROTORsoft de abril 2026 (nombre original de descarga)
RUTA_LOGBOOK_CG  = os.path.join(CARPETA, "ROTORsoft_Cerro Grande_Logbook Entries_1779820762.xlsx")
RUTA_LOGBOOK_PSP = os.path.join(CARPETA, "ROTORsoft_Peralta I  (5852)_Logbook Entries_1779820857.xlsx")


def probar():
    sesion = FabricaSesion()
    servicio = ServicioCarga(sesion)

    print("=" * 60); print("SEED CG — inspecciones"); print("=" * 60)
    print(servicio.cargar_seed_rodamientos(RUTA_RODAMIENTOS_CG, "CG", "Cerro_Grande_Actualizacion_Rodamientos.xlsx"))

    print("\n" + "=" * 60); print("SEED PSP — inspecciones"); print("=" * 60)
    print(servicio.cargar_seed_rodamientos(RUTA_RODAMIENTOS_PSP, "PSP", "Peralta_Actualizacion_Rodamientos.xlsx"))

    print("\n" + "=" * 60); print("SEED PSP — warnings historicos"); print("=" * 60)
    print(servicio.cargar_seed_warnings_peralta(RUTA_SEED_WARNINGS_PSP, "seed_rodamientos_psp.xlsx"))

    print("\n" + "=" * 60); print("LOGBOOK CG — abril 2026"); print("=" * 60)
    print(servicio.cargar_logbook(RUTA_LOGBOOK_CG, "CG", "ROTORsoft_Cerro_Grande_abril.xlsx"))

    print("\n" + "=" * 60); print("LOGBOOK PSP — abril 2026"); print("=" * 60)
    print(servicio.cargar_logbook(RUTA_LOGBOOK_PSP, "PSP", "ROTORsoft_Peralta_abril.xlsx"))

    sesion.close()
    print("\n✓ Prueba completa")


if __name__ == "__main__":
    probar()