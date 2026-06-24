from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.dependencias import obtener_sesion
from app.repositorios.repositorio_parque import RepositorioParque
from app.repositorios.repositorio_inspeccion import RepositorioInspeccion
from app.repositorios.repositorio_warning_por_tipo import RepositorioWarningPorTipo
from app.repositorios.repositorio_warning_por_mes import RepositorioWarningPorMes
from app.repositorios.repositorio_turbina import RepositorioTurbina

router = APIRouter(prefix="/resumen", tags=["resumen"])

@router.get("/{codigo_parque}")
def resumen(codigo_parque: str, sesion: Session = Depends(obtener_sesion)):
    parque = RepositorioParque(sesion).obtener_por_codigo(codigo_parque.upper())
    if not parque:
        raise HTTPException(status_code=404, detail="Parque no encontrado")

    # Contadores A/B/C/D desde la ultima inspeccion de cada turbina
    ultimas = RepositorioInspeccion(sesion).obtener_ultimas_por_parque(parque.id)
    contadores_del = {"A": 0, "B": 0, "C": 0, "D": 0, "ND": 0}
    contadores_tras = {"A": 0, "B": 0, "C": 0, "D": 0, "ND": 0}
    for insp in ultimas:
        cat_del = insp.categoria_delantera if insp.categoria_delantera in contadores_del else "ND"
        cat_tras = insp.categoria_trasera if insp.categoria_trasera in contadores_tras else "ND"
        contadores_del[cat_del] += 1
        contadores_tras[cat_tras] += 1

    # Warnings por tipo con granularidad de mes/anio para filtrado client-side
    filas_tipo = RepositorioWarningPorTipo(sesion).obtener_todas_por_parque(parque.id)
    warnings_por_tipo = [
        {"tipo": f.tipo, "cantidad": f.cantidad, "mes": f.mes, "anio": f.anio}
        for f in filas_tipo
    ]

    # Warnings por mes
    filas_mes = RepositorioWarningPorMes(sesion).obtener_totales_por_mes(parque.id)
    warnings_por_mes = [{"mes": f.mes, "anio": f.anio, "total": f.total} for f in filas_mes]

    # Detalle por turbina para gráficos Rodamiento ≠ A
    turbinas_parque   = RepositorioTurbina(sesion).obtener_todos(parque.id)
    turbina_por_id    = {t.id: t for t in turbinas_parque}
    ultima_por_turbina = {insp.turbina_id: insp for insp in ultimas}

    detalle: dict = {}
    for fila in filas_tipo:
        tid = fila.turbina_id
        if tid not in detalle:
            t    = turbina_por_id.get(tid)
            insp = ultima_por_turbina.get(tid)
            if not t:
                continue
            detalle[tid] = {
                "turbina_codigo":      t.codigo,
                "turbina_id":          tid,
                "categoria_delantera": insp.categoria_delantera if insp else "ND",
                "categoria_trasera":   insp.categoria_trasera   if insp else "ND",
                "warnings": [],
            }
        detalle[tid]["warnings"].append({
            "tipo":     fila.tipo,
            "cantidad": fila.cantidad,
            "mes":      fila.mes,
            "anio":     fila.anio,
        })

    warnings_detalle_turbinas = sorted(detalle.values(), key=lambda x: x["turbina_codigo"])

    return {
        "parque": {"id": parque.id, "nombre": parque.nombre, "codigo": parque.codigo},
        "contadores": {
            "delantera": contadores_del,
            "trasera": contadores_tras,
        },
        "warnings_por_tipo": warnings_por_tipo,
        "warnings_por_mes": warnings_por_mes,
        "warnings_detalle_turbinas": warnings_detalle_turbinas,
    }