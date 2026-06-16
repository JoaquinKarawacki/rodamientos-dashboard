from sqlalchemy.orm import Session
from app.modelos.parque import Parque

class RepositorioParque:
    def __init__(self, sesion: Session):
        self.sesion = sesion

    def obtener_todos(self) -> list[Parque]:
        return self.sesion.query(Parque).order_by(Parque.id).all()

    def obtener_por_codigo(self, codigo: str) -> Parque | None:
        return self.sesion.query(Parque).filter_by(codigo=codigo).first()    