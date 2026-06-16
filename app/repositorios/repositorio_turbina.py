from sqlalchemy.orm import Session
from app.modelos.turbina import Turbina


class RepositorioTurbina:
    def __init__(self, sesion: Session):
        self.sesion = sesion

    def obtener_por_codigo(self, parque_id: int, codigo: str) -> Turbina | None:
        return (
            self.sesion.query(Turbina)
            .filter_by(parque_id=parque_id, codigo=codigo)
            .first()
        )

    def obtener_todos(self, parque_id: int) -> list[Turbina]:
        return (
            self.sesion.query(Turbina)
            .filter_by(parque_id=parque_id, activa=True)
            .order_by(Turbina.numero)
            .all()
        )
    
    def obtener_por_id(self, turbina_id: int) -> Turbina | None:
        return self.sesion.query(Turbina).filter_by(id=turbina_id).first()