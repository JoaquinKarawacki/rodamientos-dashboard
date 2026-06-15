from sqlalchemy.orm import Session
from app.modelos.warning_por_mes import WarningPorMes


class RepositorioWarningPorMes:
    def __init__(self, sesion: Session):
        self.sesion = sesion

    def insertar_si_no_existe(self, turbina_id: int, datos: dict, carga_id: int) -> bool:
        """
        Inserta el conteo mensual solo si no existe ya uno para esa
        (turbina, mes, anio). Retorna True si inserto, False si ya existia.

        Esto es lo que protege contra el doble conteo: si por error se
        carga un mes que ya estaba (ej. un logbook que pisa el seed de
        Peralta), el registro existente se respeta y no se suma de nuevo.
        """
        existente = (
            self.sesion.query(WarningPorMes)
            .filter_by(turbina_id=turbina_id, mes=datos["mes"], anio=datos["anio"])
            .first()
        )

        if existente:
            return False

        nuevo = WarningPorMes(
            turbina_id=turbina_id,
            carga_id=carga_id,
            mes=datos["mes"],
            anio=datos["anio"],
            cantidad=datos["cantidad"],
        )
        self.sesion.add(nuevo)
        return True

    def eliminar_por_carga(self, carga_id: int) -> int:
        """Borra todos los conteos de una carga. Usado al revertir."""
        return (
            self.sesion.query(WarningPorMes)
            .filter_by(carga_id=carga_id)
            .delete()
        )