from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os
from app.rutas import exportar, inspecciones, parques, mapa_estado, resumen, turbina, admin

app = FastAPI(title="Dashboard de Rodamientos")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(parques.router)
app.include_router(mapa_estado.router)
app.include_router(resumen.router)
app.include_router(turbina.router)
app.include_router(admin.router)
app.include_router(inspecciones.router)
app.include_router(exportar.router)
        

@app.get("/")
def raiz():
    html_path = os.path.join(os.path.dirname(__file__), "dashboard.html")
    return FileResponse(html_path, media_type="text/html")