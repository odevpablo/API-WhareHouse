from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.services.cluster_service import ClusterService
from app.models.cluster import ClusterCreate, IMEIData

router = APIRouter(
    prefix="/api/clusters",
    tags=["clusters"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=dict)
def create_cluster(
    nome: str,
    imeis: List[str],
    descricao: str = "",
    db: Session = Depends(get_db)
):
    """
    Cria um novo cluster com os IMEIs fornecidos
    
    - **nome**: Nome do cluster
    - **imeis**: Lista de IMEIs para incluir no cluster
    - **descricao**: Descrição opcional do cluster
    """
    service = ClusterService(db)
    try:
        return service.create_cluster(nome, imeis, descricao)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[dict])
def list_clusters(db: Session = Depends(get_db)):
    """Lista todos os clusters existentes"""
    service = ClusterService(db)
    return service.list_clusters()

@router.get("/{cluster_id}", response_model=dict)
def get_cluster(cluster_id: str, db: Session = Depends(get_db)):
    """Obtém os detalhes de um cluster específico"""
    service = ClusterService(db)
    cluster = service.get_cluster(cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster não encontrado")
    return cluster

@router.get("/{cluster_id}/imeis", response_model=List[dict])
def get_cluster_imeis(cluster_id: str, db: Session = Depends(get_db)):
    """Lista todos os IMEIs de um cluster específico"""
    service = ClusterService(db)
    imeis = service.get_imeis_from_cluster(cluster_id)
    if not imeis:
        raise HTTPException(status_code=404, detail="Nenhum IMEI encontrado para este cluster")
    return imeis
