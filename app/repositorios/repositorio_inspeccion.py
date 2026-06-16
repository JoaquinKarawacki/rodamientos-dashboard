from sqlalchemy.orm import Session
from app.modelos.inspeccion_rodamiento import InspeccionRodamiento
from sqlalchemy import func
from app.modelos.turbina import Turbina


class RepositorioInspeccion:
    def __init__(self, sesion: Session):
        self.sesion = sesion

    def insertar_si_no_existe(self, turbina_id: int, datos: dict, carga_id: int) -> bool:
        """
        Inserta la inspeccion solo si no hay ya una con la misma
        (turbina_id, fecha). Retorna True si inserto, False si ya existia.
        """
        existente = (
            self.sesion.query(InspeccionRodamiento)
            .filter_by(turbina_id=turbina_id, fecha=datos["fecha"])
            .first()
        )

        if existente:
            return False

        nueva = InspeccionRodamiento(
            turbina_id=turbina_id,
            carga_id=carga_id,
            **datos
        )
        self.sesion.add(nueva)
        return True

    def obtener_ultima_por_turbina(self, turbina_id: int) -> InspeccionRodamiento | None:
        return (
            self.sesion.query(InspeccionRodamiento)
            .filter_by(turbina_id=turbina_id)
            .order_by(InspeccionRodamiento.fecha.desc())
            .first()
        )

    def eliminar_por_carga(self, carga_id: int) -> int:
        """Elimina todos los registros de una carga. Usado al revertir."""
        return (
            self.sesion.query(InspeccionRodamiento)
            .filter_by(carga_id=carga_id)
            .delete()
        )

    def obtener_ultimas_por_parque(self, parque_id: int) -> list[InspeccionRodamiento]:
        subq = (
            self.sesion.query(
                InspeccionRodamiento.turbina_id,
                func.max(InspeccionRodamiento.fecha).label("max_fecha")
            )
            .join(Turbina)
            .filter(Turbina.parque_id == parque_id)
            .group_by(InspeccionRodamiento.turbina_id)
            .subquery()
        )
        return (
            self.sesion.query(InspeccionRodamiento)
            .join(subq, (InspeccionRodamiento.turbina_id == subq.c.turbina_id) &
                        (InspeccionRodamiento.fecha == subq.c.max_fecha))
            .all()
        )
    
    def obtener_por_turbina(self, turbina_id: int) -> list[InspeccionRodamiento]:
        return (
            self.sesion.query(InspeccionRodamiento)
            .filter_by(turbina_id=turbina_id)
            .order_by(InspeccionRodamiento.fecha.desc())
            .all()
        )

    def obtener_por_id(self, insp_id: int) -> InspeccionRodamiento | None:
        return self.sesion.query(InspeccionRodamiento).filter_by(id=insp_id).first()

    def actualizar(self, insp_id: int, datos: dict) -> InspeccionRodamiento | None:
        insp = self.obtener_por_id(insp_id)
        if not insp:
            return None
        for campo, valor in datos.items():
            setattr(insp, campo, valor)
        return insp

    def eliminar_por_id(self, insp_id: int) -> bool:
        insp = self.obtener_por_id(insp_id)
        if not insp:
            return False
        self.sesion.delete(insp)
        return True 
    
    def obtener_todas_por_parque(self, parque_id: int) -> list[InspeccionRodamiento]:
        return (
            self.sesion.query(InspeccionRodamiento)
            .join(Turbina)
            .filter(Turbina.parque_id == parque_id)
            .order_by(InspeccionRodamiento.fecha.desc())
            .all()
        )
