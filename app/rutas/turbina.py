from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.dependencias import obtener_sesion
from app.repositorios.repositorio_turbina import RepositorioTurbina
from app.repositorios.repositorio_inspeccion import RepositorioInspeccion
from app.repositorios.repositorio_warning_por_mes import RepositorioWarningPorMes
from app.repositorios.repositorio_warning_por_tipo import RepositorioWarningPorTipo

router = APIRouter(prefix="/turbina", tags=["turbina"])

@router.get("/{turbina_id}")
def detalle_turbina(turbina_id: int, sesion: Session = Depends(obtener_sesion)):
    turbina = RepositorioTurbina(sesion).obtener_por_id(turbina_id)
    if not turbina:
        raise HTTPException(status_code=404, detail="Turbina no encontrada")

    inspecciones = RepositorioInspeccion(sesion).obtener_por_turbina(turbina_id)
    warnings_mes = RepositorioWarningPorMes(sesion).obtener_por_turbina(turbina_id)
    warnings_tipo = RepositorioWarningPorTipo(sesion).obtener_por_turbina(turbina_id)

    return {
        "turbina": {
            "id": turbina.id,
            "codigo": turbina.codigo,
            "numero": turbina.numero,
            "parque_id": turbina.parque_id,
        },
        "inspecciones": [
            {
                "id": i.id,
                "fecha": str(i.fecha),
                "tipo_evento": i.tipo_evento,
                "categoria_delantera": i.categoria_delantera,
                "categoria_trasera": i.categoria_trasera,
                "cambio_rodamiento_delantero": str(i.cambio_rodamiento_delantero) if i.cambio_rodamiento_delantero else None,
                "cambio_rodamiento_trasero": str(i.cambio_rodamiento_trasero) if i.cambio_rodamiento_trasero else None,
                "comentarios": i.comentarios,
            }
            for i in inspecciones
        ],
        "warnings_por_mes": [
            {"mes": w.mes, "anio": w.anio, "cantidad": w.cantidad}
            for w in warnings_mes
        ],
        "warnings_por_tipo": [
            {"tipo": w.tipo, "cantidad": w.cantidad, "mes": w.mes, "anio": w.anio}
            for w in warnings_tipo
        ],
    }