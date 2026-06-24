import sys
sys.path.insert(0, '.')
from app.database import FabricaSesion
from app.servicios.servicio_carga import ServicioCarga

sesion = FabricaSesion()
resultado = ServicioCarga(sesion).cargar_seed_rodamientos(
    'scripts/Peralta_Actualizacion_Rodamientos .xlsx',
    'PSP',
    'Peralta_Actualizacion_Rodamientos.xlsx'
)
print(resultado)
sesion.close()
