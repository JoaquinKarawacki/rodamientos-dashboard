from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class Carga(Base):
    """
    Audit trail de cada Excel subido al sistema.
    Si una carga fue incorrecta, se puede revertir eliminando todos
    los registros con ese carga_id, sin tocar nada más.
    """
    __tablename__ = "cargas"

    id                  = Column(Integer, primary_key=True)
    parque_id           = Column(Integer, ForeignKey("parques.id"), nullable=False)
    tipo_archivo        = Column(String(20), nullable=False)   # "rodamientos" | "logbook"
    nombre_archivo      = Column(String(255), nullable=False)
    fecha_carga         = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    estado              = Column(String(20), default="exitosa")  # "exitosa" | "fallida" | "revertida"
    registros_insertados = Column(Integer, default=0)
    notas               = Column(String(500), nullable=True)

    parque       = relationship("Parque", back_populates="cargas")
    inspecciones = relationship("InspeccionRodamiento", back_populates="carga")
    warnings_por_mes  = relationship("WarningPorMes",  back_populates="carga")
    warnings_por_tipo = relationship("WarningPorTipo", back_populates="carga")