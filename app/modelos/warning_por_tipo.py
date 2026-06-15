from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class WarningPorTipo(Base):
    """
    Conteo de warnings de rodamiento por turbina y tipo.
    - Peralta (seed): hoja Warnings_por_Tipo. Es acumulado de todo el
      periodo, por eso mes y anio quedan nulos.
    - Logbook mensual (ambos parques): se llena agregando los eventos
      clasificados por tipo, con su mes y anio.

    mes y anio nullable a proposito: distinguen el acumulado historico
    de Peralta (sin mes) de los conteos mensuales del logbook.
    """
    __tablename__ = "warnings_por_tipo"

    id         = Column(Integer, primary_key=True)
    turbina_id = Column(Integer, ForeignKey("turbinas.id"), nullable=False)
    carga_id   = Column(Integer, ForeignKey("cargas.id"),   nullable=False)
    tipo       = Column(String(50), nullable=False)
    cantidad   = Column(Integer, nullable=False, default=0)
    mes        = Column(Integer, nullable=True)        # null = acumulado historico
    anio       = Column(Integer, nullable=True)
    fecha_creacion = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    turbina = relationship("Turbina", back_populates="warnings_por_tipo")
    carga   = relationship("Carga",   back_populates="warnings_por_tipo")

    __table_args__ = (
        UniqueConstraint("turbina_id", "tipo", "mes", "anio",
                         name="uq_warning_tipo_turbina_tipo_periodo"),
    )