from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class WarningRodamiento(Base):
    __tablename__ = "warnings_rodamientos"

    id            = Column(Integer, primary_key=True)
    turbina_id    = Column(Integer, ForeignKey("turbinas.id"), nullable=False)
    carga_id      = Column(Integer, ForeignKey("cargas.id"),   nullable=False)
    fecha_inicio  = Column(DateTime, nullable=False)
    fecha_fin     = Column(DateTime, nullable=True)
    mes           = Column(Integer, nullable=False)   # desnormalizado: 1-12
    anio          = Column(Integer, nullable=False)   # desnormalizado: 2025, 2026
    tipo_warning  = Column(String(50), nullable=False)  # "Lub. Sin presion", "Grasa vacio", etc.
    descripcion   = Column(String(500), nullable=True)  # texto original del evento
    duracion_horas = Column(Float, nullable=True)
    potencia_kw   = Column(Float, nullable=True)
    viento_ms     = Column(Float, nullable=True)
    fecha_creacion = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    turbina = relationship("Turbina", back_populates="warnings")
    carga   = relationship("Carga",   back_populates="warnings")

    __table_args__ = (
        UniqueConstraint("turbina_id", "fecha_inicio", "tipo_warning",
                         name="uq_warning_turbina_fecha_tipo"),
    )