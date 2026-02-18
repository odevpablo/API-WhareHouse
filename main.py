from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv

from app.routes import imei as imei_router
from app.routes import cluster_routes
from app.database import get_db, engine
import app.models.dispositivos as models
from app.models.cluster import Base as ClusterBase

# Carrega as variáveis de ambiente
load_dotenv()

app = FastAPI(
    title="Sistema de Gerenciamento de Clusters de IMEI",
    description="API para gerenciamento de clusters de dispositivos por IMEI",
    version="1.0.0"
)

# Evento de inicialização
@app.on_event("startup")
async def startup_event():
    # Cria as tabelas no banco de dados
    models.Base.metadata.create_all(bind=engine)
    ClusterBase.metadata.create_all(bind=engine)

# Configuração do CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite todas as origens temporariamente
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclui os roteadores
app.include_router(imei_router.router)
app.include_router(cluster_routes.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)