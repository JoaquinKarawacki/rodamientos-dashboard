from sqlalchemy import Column, Integer, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class WarningPorMes(Base):
    """
    Conteo de warnings de rodamiento por turbina y mes.
    - Peralta (seed): se llena de la hoja Warnings_Mensuales.
    - Logbook mensual (ambos parques): se llena agregando los eventos
      clasificados, contando cuantos hubo en cada mes.
    """
    __tablename__ = "warnings_por_mes"

    id         = Column(Integer, primary_key=True)
    turbina_id = Column(Integer, ForeignKey("turbinas.id"), nullable=False)
    carga_id   = Column(Integer, ForeignKey("cargas.id"),   nullable=False)
    mes        = Column(Integer, nullable=False)   # 1-12
    anio       = Column(Integer, nullable=False)   # 2025, 2026
    cantidad   = Column(Integer, nullable=False, default=0)
    fecha_creacion = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    turbina = relationship("Turbina", back_populates="warnings_por_mes")
    carga   = relationship("Carga",   back_populates="warnings_por_mes")

    __table_args__ = (
        UniqueConstraint("turbina_id", "mes", "anio",
                         name="uq_warning_mes_turbina_periodo"),
    )