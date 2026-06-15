from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class InspeccionRodamiento(Base):
    __tablename__ = "inspecciones_rodamientos"

    id                         = Column(Integer, primary_key=True)
    turbina_id                 = Column(Integer, ForeignKey("turbinas.id"), nullable=False)
    carga_id                   = Column(Integer, ForeignKey("cargas.id"),   nullable=False)
    fecha                      = Column(Date, nullable=False)
    tipo_evento                = Column(String(100), nullable=False)  # "Mant. 4 años 2025"
    categoria_delantera        = Column(String(5), nullable=False)    # "A", "B", "C", "D", "ND"
    categoria_trasera          = Column(String(5), nullable=False)
    cambio_rodamiento_delantero = Column(Date, nullable=True)
    cambio_rodamiento_trasero   = Column(Date, nullable=True)
    comentarios                = Column(String(500), nullable=True)
    fecha_creacion             = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    turbina = relationship("Turbina", back_populates="inspecciones")
    carga   = relationship("Carga",   back_populates="inspecciones")

    __table_args__ = (
        UniqueConstraint("turbina_id", "fecha", name="uq_inspeccion_turbina_fecha"),
    )