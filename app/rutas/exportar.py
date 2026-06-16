import json
import os
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.dependencias import obtener_sesion
from app.repositorios.repositorio_parque import RepositorioParque
from app.repositorios.repositorio_turbina import RepositorioTurbina
from app.repositorios.repositorio_inspeccion import RepositorioInspeccion
from app.repositorios.repositorio_warning_por_mes import RepositorioWarningPorMes
from app.repositorios.repositorio_warning_por_tipo import RepositorioWarningPorTipo

router = APIRouter(prefix="/exportar", tags=["exportar"])

@router.get("/{codigo_parque}", response_class=HTMLResponse)
def exportar_dashboard(codigo_parque: str, sesion: Session = Depends(obtener_sesion)):
    parque = RepositorioParque(sesion).obtener_por_codigo(codigo_parque.upper())
    if not parque:
        raise HTTPException(status_code=404, detail="Parque no encontrado")

    turbinas      = RepositorioTurbina(sesion).obtener_todos(parque.id)
    all_insp      = RepositorioInspeccion(sesion).obtener_todas_por_parque(parque.id)
    all_warn_mes  = RepositorioWarningPorMes(sesion).obtener_todas_por_parque(parque.id)
    all_warn_tipo = RepositorioWarningPorTipo(sesion).obtener_todas_por_parque(parque.id)

    insp_idx      = {}
    for i in all_insp:
        insp_idx.setdefault(i.turbina_id, []).append(i)

    warn_mes_idx  = {}
    for w in all_warn_mes:
        warn_mes_idx.setdefault(w.turbina_id, []).append(w)

    warn_tipo_idx = {}
    for w in all_warn_tipo:
        warn_tipo_idx.setdefault(w.turbina_id, []).append(w)

    turbinas_data = []
    contadores_del  = {"A": 0, "B": 0, "C": 0, "D": 0, "ND": 0}
    contadores_tras = {"A": 0, "B": 0, "C": 0, "D": 0, "ND": 0}

    for t in turbinas:
        inspecciones = insp_idx.get(t.id, [])
        ultima = inspecciones[0] if inspecciones else None

        tipo_agg = {}
        for w in warn_tipo_idx.get(t.id, []):
            tipo_agg[w.tipo] = tipo_agg.get(w.tipo, 0) + w.cantidad

        turbinas_data.append({
            "id": t.id,
            "codigo": t.codigo,
            "numero": t.numero,
            "ultima_inspeccion": {
                "fecha": str(ultima.fecha),
                "tipo_evento": ultima.tipo_evento,
                "categoria_delantera": ultima.categoria_delantera,
                "categoria_trasera": ultima.categoria_trasera,
            } if ultima else None,
            "inspecciones": [
                {
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
                for w in warn_mes_idx.get(t.id, [])
            ],
            "warnings_por_tipo": [
                {"tipo": tipo, "cantidad": cant}
                for tipo, cant in sorted(tipo_agg.items())
            ],
        })

        if ultima:
            cd = ultima.categoria_delantera if ultima.categoria_delantera in contadores_del else "ND"
            ct = ultima.categoria_trasera if ultima.categoria_trasera in contadores_tras else "ND"
            contadores_del[cd] += 1
            contadores_tras[ct] += 1

    warn_mes_global = {}
    for w in all_warn_mes:
        key = (w.mes, w.anio)
        warn_mes_global[key] = warn_mes_global.get(key, 0) + w.cantidad

    warn_tipo_global = {}
    for w in all_warn_tipo:
        warn_tipo_global[w.tipo] = warn_tipo_global.get(w.tipo, 0) + w.cantidad

    data = {
        "parque": {
            "id": parque.id,
            "nombre": parque.nombre,
            "codigo": parque.codigo,
            "cantidad_turbinas": parque.cantidad_turbinas,
        },
        "turbinas": turbinas_data,
        "resumen": {
            "contadores": {
                "delantera": contadores_del,
                "trasera": contadores_tras,
            },
            "warnings_por_mes": [
                {"mes": mes, "anio": anio, "total": total}
                for (mes, anio), total in sorted(warn_mes_global.items(), key=lambda x: (x[0][1], x[0][0]))
            ],
            "warnings_por_tipo": [
                {"tipo": tipo, "total": total}
                for tipo, total in sorted(warn_tipo_global.items())
            ],
        },
        "generado": datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC"),
    }

    json_str = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")

    template_path = os.path.join(os.path.dirname(__file__), "..", "templates", "standalone.html")
    with open(template_path, encoding="utf-8") as f:
        html = f.read()

    html = html.replace("__DASHBOARD_DATA__", json_str)

    nombre = f"rodamientos_{parque.codigo.lower()}_{datetime.now().strftime('%Y%m%d')}.html"
    return HTMLResponse(
        content=html,
        headers={"Content-Disposition": f'attachment; filename="{nombre}"'},
    )