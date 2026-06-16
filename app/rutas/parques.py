from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.dependencias import obtener_sesion
from app.repositorios.repositorio_parque import RepositorioParque

router = APIRouter(prefix="/parques", tags=["parques"])

@router.get("/")
def listar_parques(sesion: Session = Depends(obtener_sesion)):
    repo = RepositorioParque(sesion)
    parques = repo.obtener_todos()
    return [
        {
            "id": p.id,
            "nombre": p.nombre,
            "codigo": p.codigo,
            "cantidad_turbinas": p.cantidad_turbinas,
        }
        for p in parques
    ]