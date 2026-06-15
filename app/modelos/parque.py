from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class Parque(Base):
    __tablename__ = "parques"

    id               = Column(Integer, primary_key=True)
    nombre           = Column(String(100), nullable=False)          # "Cerro Grande"
    codigo           = Column(String(10), nullable=False, unique=True)  # "CG", "PSP"
    cantidad_turbinas = Column(Integer, nullable=False)
    fecha_creacion   = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    turbinas = relationship("Turbina", back_populates="parque")
    cargas   = relationship("Carga",   back_populates="parque")