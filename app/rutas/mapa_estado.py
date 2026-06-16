from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.dependencias import obtener_sesion
from app.repositorios.repositorio_parque import RepositorioParque
from app.repositorios.repositorio_turbina import RepositorioTurbina
from app.repositorios.repositorio_inspeccion import RepositorioInspeccion

router = APIRouter(prefix="/mapa-estado", tags=["mapa-estado"])

@router.get("/{codigo_parque}")
def mapa_estado(codigo_parque: str, sesion: Session = Depends(obtener_sesion)):
    parque = RepositorioParque(sesion).obtener_por_codigo(codigo_parque.upper())
    if not parque:
        raise HTTPException(status_code=404, detail="Parque no encontrado")

    turbinas = RepositorioTurbina(sesion).obtener_todos(parque.id)
    ultimas = RepositorioInspeccion(sesion).obtener_ultimas_por_parque(parque.id)

    # Indexamos por turbina_id para lookup O(1)
    inspeccion_por_turbina = {i.turbina_id: i for i in ultimas}

    resultado = []
    for t in turbinas:
        insp = inspeccion_por_turbina.get(t.id)
        resultado.append({
            "id": t.id,
            "codigo": t.codigo,
            "numero": t.numero,
            "ultima_inspeccion": {
                "fecha": str(insp.fecha),
                "tipo_evento": insp.tipo_evento,
                "categoria_delantera": insp.categoria_delantera,
                "categoria_trasera": insp.categoria_trasera,
            } if insp else None,
        })

    return {"parque": {"id": parque.id, "nombre": parque.nombre, "codigo": parque.codigo}, "turbinas": resultado}