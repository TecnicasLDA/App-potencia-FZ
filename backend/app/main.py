import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .api import endpoints

# Solo crear tablas automaticamente cuando se habilite explicitamente.
auto_create_tables = os.getenv("AUTO_CREATE_TABLES", "false").lower() == "true"
if auto_create_tables:
    Base.metadata.create_all(bind=engine)

# Inicializar FastAPI
app = FastAPI(
    title="API Potencia Zuccardi",
    description="Visualizador de potencia contratada vs demandada",
    version="1.0.0"
)

cors_origins_env = os.getenv("CORS_ORIGINS", "*")
cors_origins = [origin.strip() for origin in cors_origins_env.split(",") if origin.strip()]
if not cors_origins:
    cors_origins = ["*"]

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers de API
app.include_router(endpoints.router)

# Health check
@app.get("/")
def root():
    return {
        "nombre": "API Potencia Zuccardi",
        "descripcion": "Sistema de visualización de potencia contratada vs demandada",
        "endpoints": {
            "filtros": "/api/filtros",
            "cascada": "/api/filtros/cascada",
            "grafico": "/api/grafico/{nic}",
            "salud": "/api/salud"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
