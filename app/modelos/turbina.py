from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Turbina(Base):
    __tablename__ = "turbinas"

    id        = Column(Integer, primary_key=True)
    parque_id = Column(Integer, ForeignKey("parques.id"), nullable=False)
    codigo    = Column(String(20), nullable=False)   # "WEC01", "PSP-01"
    numero    = Column(Integer, nullable=False)       # 1, 2, ... 22 ó 50
    activa    = Column(Boolean, default=True)

    parque         = relationship("Parque",  back_populates="turbinas")
    inspecciones   = relationship("InspeccionRodamiento", back_populates="turbina")
    warnings_por_mes  = relationship("WarningPorMes",  back_populates="turbina")
    warnings_por_tipo = relationship("WarningPorTipo", back_populates="turbina")