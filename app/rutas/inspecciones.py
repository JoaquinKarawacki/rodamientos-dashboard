from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import date
from typing import Optional
from app.dependencias import obtener_sesion
from app.repositorios.repositorio_inspeccion import RepositorioInspeccion

router = APIRouter(prefix="/inspeccion", tags=["inspecciones"])

class InspeccionUpdate(BaseModel):
    tipo_evento: Optional[str] = None
    categoria_delantera: Optional[str] = None
    categoria_trasera: Optional[str] = None
    cambio_rodamiento_delantero: Optional[date] = None
    cambio_rodamiento_trasero: Optional[date] = None
    comentarios: Optional[str] = None

@router.put("/{insp_id}")
def editar_inspeccion(insp_id: int, datos: InspeccionUpdate, sesion: Session = Depends(obtener_sesion)):
    repo = RepositorioInspeccion(sesion)
    campos = {k: v for k, v in datos.model_dump().items() if v is not None}
    if not campos:
        raise HTTPException(status_code=400, detail="No se enviaron campos para actualizar")
    insp = repo.actualizar(insp_id, campos)
    if not insp:
        raise HTTPException(status_code=404, detail="Inspección no encontrada")
    try:
        sesion.commit()
        return {"estado": "actualizada", "id": insp_id}
    except Exception as e:
        sesion.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{insp_id}")
def eliminar_inspeccion(insp_id: int, sesion: Session = Depends(obtener_sesion)):
    repo = RepositorioInspeccion(sesion)
    if not repo.eliminar_por_id(insp_id):
        raise HTTPException(status_code=404, detail="Inspección no encontrada")
    try:
        sesion.commit()
        return {"estado": "eliminada", "id": insp_id}
    except Exception as e:
        sesion.rollback()
        raise HTTPException(status_code=400, detail=str(e))