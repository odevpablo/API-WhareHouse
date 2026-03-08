from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

from app.routes import imei as imei_router
from app.routes import cluster_routes
from app.routes import kanban as kanban_router
from app.database import get_db, engine
import app.models.dispositivos as models
from app.models.cluster import Base as ClusterBase
from app.models.tarefa import Base as TarefaBase

# Carrega as variáveis de ambiente
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Código de inicialização
    models.Base.metadata.create_all(bind=engine)
    ClusterBase.metadata.create_all(bind=engine)
    TarefaBase.metadata.create_all(bind=engine)
    yield
    # Código de limpeza (se necessário)

app = FastAPI(
    title="Sistema de Gerenciamento de Clusters de IMEI",
    description="API para gerenciamento de clusters de dispositivos por IMEI",
    version="1.0.0",
    lifespan=lifespan
)

# Configuração do CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite todas as origens temporariamente
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclui os roteadores com o prefixo /api
app.include_router(imei_router.router, prefix="/api", tags=["IMEI"])
app.include_router(cluster_routes.router, prefix="/api", tags=["Clusters"])
app.include_router(kanban_router.router, prefix="/api", tags=["Kanban"])

@app.get("/")
async def root():
    return {
        "message": "API de Gerenciamento de Clusters de IMEI",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "kanban": "/api/tarefas",
            "imei": "/api/consultar",
            "clusters": "/api/clusters"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)