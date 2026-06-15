from sqlalchemy.orm import Session
from app.modelos.carga import Carga


class RepositorioCarga:
    def __init__(self, sesion: Session):
        self.sesion = sesion

    def crear(self, parque_id: int, tipo: str, nombre: str) -> Carga:
        carga = Carga(
            parque_id=parque_id,
            tipo_archivo=tipo,
            nombre_archivo=nombre,
        )
        self.sesion.add(carga)
        self.sesion.flush()  # obtiene el ID sin hacer commit todavia
        return carga

    def obtener_por_parque(self, parque_id: int) -> list[Carga]:
        return (
            self.sesion.query(Carga)
            .filter_by(parque_id=parque_id)
            .order_by(Carga.fecha_carga.desc())
            .all()
        )