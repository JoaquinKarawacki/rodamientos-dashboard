import os
import tempfile
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.dependencias import obtener_sesion
from app.repositorios.repositorio_parque import RepositorioParque
from app.repositorios.repositorio_carga import RepositorioCarga
from app.servicios.servicio_carga import ServicioCarga

router = APIRouter(prefix="/admin", tags=["admin"])

TIPOS_VALIDOS = ["seed_rodamientos", "control_mensual", "logbook", "seed_warnings"]

@router.get("/cargas/{codigo_parque}")
def listar_cargas(codigo_parque: str, sesion: Session = Depends(obtener_sesion)):
    parque = RepositorioParque(sesion).obtener_por_codigo(codigo_parque.upper())
    if not parque:
        raise HTTPException(status_code=404, detail="Parque no encontrado")
    cargas = RepositorioCarga(sesion).obtener_por_parque(parque.id)
    return [
        {
            "id": c.id,
            "tipo_archivo": c.tipo_archivo,
            "nombre_archivo": c.nombre_archivo,
            "fecha_carga": c.fecha_carga.isoformat() if c.fecha_carga else None,
            "estado": c.estado,
            "registros_insertados": c.registros_insertados,
        }
        for c in cargas
    ]

@router.post("/cargar")
async def cargar_archivo(
    archivo: UploadFile = File(...),
    codigo_parque: str = Form(...),
    tipo_carga: str = Form(...),
    sesion: Session = Depends(obtener_sesion),
):
    if tipo_carga not in TIPOS_VALIDOS:
        raise HTTPException(status_code=400, detail=f"tipo_carga debe ser uno de: {TIPOS_VALIDOS}")
    if tipo_carga == "seed_warnings" and codigo_parque.upper() != "PSP":
        raise HTTPException(status_code=400, detail="seed_warnings solo aplica al parque PSP")

    suffix = os.path.splitext(archivo.filename)[1] or ".xlsx"
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(archivo.file, tmp)
            tmp_path = tmp.name

        servicio = ServicioCarga(sesion)
        codigo = codigo_parque.upper()
        nombre = archivo.filename

        if tipo_carga == "seed_rodamientos":
            resultado = servicio.cargar_seed_rodamientos(tmp_path, codigo, nombre)
        elif tipo_carga == "control_mensual":
            resultado = servicio.cargar_control_mensual(tmp_path, codigo, nombre)
        elif tipo_carga == "logbook":
            resultado = servicio.cargar_logbook(tmp_path, codigo, nombre)
        elif tipo_carga == "seed_warnings":
            resultado = servicio.cargar_seed_warnings_peralta(tmp_path, nombre)

        return resultado
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

@router.delete("/carga/{carga_id}")
def revertir_carga(carga_id: int, sesion: Session = Depends(obtener_sesion)):
    try:
        return ServicioCarga(sesion).revertir_carga(carga_id)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))