from sqlalchemy.orm import Session
from app.modelos.inspeccion_rodamiento import InspeccionRodamiento


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