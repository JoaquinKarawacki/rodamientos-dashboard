from app.database import FabricaSesion

def obtener_sesion():
    sesion = FabricaSesion()
    try:
        yield sesion
    finally:
        sesion.close()