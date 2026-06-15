from sqlalchemy.orm import Session
from app.modelos.warning_por_tipo import WarningPorTipo


class RepositorioWarningPorTipo:
    def __init__(self, sesion: Session):
        self.sesion = sesion

    def insertar_si_no_existe(self, turbina_id: int, datos: dict, carga_id: int) -> bool:
        """
        Inserta el conteo por tipo solo si no existe ya uno para esa
        (turbina, tipo, mes, anio). El mes/anio pueden ser None en el
        caso del seed de Peralta (acumulado historico).
        """
        existente = (
            self.sesion.query(WarningPorTipo)
            .filter_by(
                turbina_id=turbina_id,
                tipo=datos["tipo"],
                mes=datos["mes"],
                anio=datos["anio"],
            )
            .first()
        )

        if existente:
            return False

        nuevo = WarningPorTipo(
            turbina_id=turbina_id,
            carga_id=carga_id,
            tipo=datos["tipo"],
            cantidad=datos["cantidad"],
            mes=datos["mes"],
            anio=datos["anio"],
        )
        self.sesion.add(nuevo)
        return True

    def eliminar_por_carga(self, carga_id: int) -> int:
        return (
            self.sesion.query(WarningPorTipo)
            .filter_by(carga_id=carga_id)
            .delete()
        )
    