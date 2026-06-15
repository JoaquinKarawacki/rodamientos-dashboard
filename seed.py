from app.database import FabricaSesion
from app.modelos.parque import Parque
from app.modelos.turbina import Turbina


def sembrar():
    sesion = FabricaSesion()

    try:
        # --- Parques ---
        cerro_grande = Parque(nombre="Cerro Grande", codigo="CG",  cantidad_turbinas=22)
        peralta      = Parque(nombre="Peralta I",    codigo="PSP", cantidad_turbinas=50)
        sesion.add_all([cerro_grande, peralta])
        sesion.flush()  # genera los IDs sin hacer commit todavía

        # --- Turbinas Cerro Grande: WEC01 a WEC22 ---
        for numero in range(1, 23):
            codigo = f"WEC{numero:02d}"
            sesion.add(Turbina(parque_id=cerro_grande.id, codigo=codigo, numero=numero))

        # --- Turbinas Peralta I: PSP-01 a PSP-50 ---
        for numero in range(1, 51):
            codigo = f"PSP-{numero:02d}"
            sesion.add(Turbina(parque_id=peralta.id, codigo=codigo, numero=numero))

        sesion.commit()
        print("✓ Parques y turbinas cargadas correctamente")
        print(f"  Cerro Grande: 22 turbinas (WEC01–WEC22)")
        print(f"  Peralta I:    50 turbinas (PSP-01–PSP-50)")

    except Exception as error:
        sesion.rollback()
        print(f"✗ Error al sembrar: {error}")
    finally:
        sesion.close()


if __name__ == "__main__":
    sembrar()