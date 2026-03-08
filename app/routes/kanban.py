from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import logging
from app.database import get_db
from app.services.tarefa_service import TarefaService
from app.models.tarefa import TarefaCreate, TarefaUpdate, TarefaResponse, TarefaStatusUpdate, TarefaDelete
from pydantic import BaseModel

# Configurar logger
logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["Kanban"],
    responses={404: {"description": "Não encontrado"}},
)

# Modelos adicionais para as requisições
class TarefaStatusUpdateRequest(BaseModel):
    status: str
    observacao: str = None

class TarefaObservacaoUpdateRequest(BaseModel):
    observacao: str

@router.get("/tarefas", response_model=List[TarefaResponse])
async def get_tarefas(db: Session = Depends(get_db)):
    """
    Retorna todas as tarefas do Kanban
    """
    logger.info("Recebida requisição para listar todas as tarefas")
    try:
        service = TarefaService(db)
        tarefas = service.get_all_tarefas()
        logger.info(f"Retornando {len(tarefas)} tarefas")
        return tarefas
    except Exception as e:
        logger.error(f"Erro ao buscar tarefas: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar tarefas: {str(e)}"
        )

@router.get("/tarefas/status/{status}", response_model=List[TarefaResponse])
async def get_tarefas_by_status(status: str, db: Session = Depends(get_db)):
    """
    Retorna tarefas filtradas por status
    Status válidos: demanda, a-fazer, em-andamento, erro, feito
    """
    service = TarefaService(db)
    tarefas = service.get_tarefas_by_status(status)
    return tarefas

@router.get("/tarefas/imei/{imei}", response_model=List[TarefaResponse])
async def get_tarefas_by_imei(imei: str, db: Session = Depends(get_db)):
    """
    Retorna tarefas filtradas por IMEI
    """
    service = TarefaService(db)
    tarefas = service.get_tarefas_by_imei(imei)
    return tarefas

@router.get("/tarefas/perfil/{perfil}", response_model=List[TarefaResponse])
async def get_tarefas_by_perfil(perfil: str, db: Session = Depends(get_db)):
    """
    Retorna tarefas filtradas por perfil
    """
    service = TarefaService(db)
    tarefas = service.get_tarefas_by_perfil(perfil)
    return tarefas

@router.get("/tarefas/{tarefa_id}", response_model=TarefaResponse)
async def get_tarefa(tarefa_id: int, db: Session = Depends(get_db)):
    """
    Retorna uma tarefa específica pelo ID
    """
    service = TarefaService(db)
    tarefa = service.get_tarefa_by_id(tarefa_id)
    if not tarefa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tarefa com ID {tarefa_id} não encontrada"
        )
    return tarefa

@router.post("/tarefas", response_model=TarefaResponse, status_code=status.HTTP_201_CREATED)
async def create_tarefa(tarefa_data: TarefaCreate, db: Session = Depends(get_db)):
    """
    Cria uma nova tarefa no Kanban
    """
    service = TarefaService(db)
    
    # Validação básica dos campos obrigatórios
    if not tarefa_data.title or not tarefa_data.imei or not tarefa_data.unidade or not tarefa_data.prazo or not tarefa_data.perfil:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Campos obrigatórios: title, imei, unidade, prazo, perfil"
        )
    
    # Validação da prioridade
    if tarefa_data.priority not in ["baixa", "media", "alta"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Prioridade inválida. Valores aceitos: baixa, media, alta"
        )
    
    # Validação do status inicial
    if tarefa_data.status not in ["demanda", "a-fazer", "em-andamento", "erro", "feito"]:
        tarefa_data.status = "demanda"  # Status padrão
    
    tarefa = service.create_tarefa(tarefa_data)
    return tarefa

@router.put("/tarefas/{tarefa_id}", response_model=TarefaResponse)
async def update_tarefa(tarefa_id: int, tarefa_data: TarefaUpdate, db: Session = Depends(get_db)):
    """
    Atualiza uma tarefa existente
    """
    service = TarefaService(db)
    tarefa = service.update_tarefa(tarefa_id, tarefa_data)
    
    if not tarefa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tarefa com ID {tarefa_id} não encontrada"
        )
    
    return tarefa

@router.patch("/tarefas/{tarefa_id}/status", response_model=TarefaResponse)
async def update_tarefa_status(tarefa_id: int, status_data: TarefaStatusUpdateRequest, db: Session = Depends(get_db)):
    """
    Atualiza apenas o status de uma tarefa (usado no drag and drop)
    """
    service = TarefaService(db)
    
    # Validação do status
    status_validos = ["demanda", "a-fazer", "em-andamento", "erro", "feito"]
    if status_data.status not in status_validos:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Status inválido. Valores aceitos: {', '.join(status_validos)}"
        )
    
    status_update = TarefaStatusUpdate(
        status=status_data.status,
        observacao=status_data.observacao
    )
    
    tarefa = service.update_tarefa_status(tarefa_id, status_update)
    
    if not tarefa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tarefa com ID {tarefa_id} não encontrada"
        )
    
    return tarefa

@router.patch("/tarefas/{tarefa_id}/observacao", response_model=TarefaResponse)
async def update_tarefa_observacao(tarefa_id: int, obs_data: TarefaObservacaoUpdateRequest, db: Session = Depends(get_db)):
    """
    Atualiza apenas a observação de uma tarefa
    """
    service = TarefaService(db)
    tarefa = service.get_tarefa_by_id(tarefa_id)
    
    if not tarefa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tarefa com ID {tarefa_id} não encontrada"
        )
    
    tarefa.observacao = obs_data.observacao
    tarefa.data_atualizacao = datetime.utcnow()
    
    db.commit()
    db.refresh(tarefa)
    
    return tarefa

@router.delete("/tarefas/{tarefa_id}")
async def delete_tarefa(tarefa_id: int, db: Session = Depends(get_db)):
    """
    Deleta uma tarefa
    """
    service = TarefaService(db)
    sucesso = service.delete_tarefa(tarefa_id)
    
    if not sucesso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tarefa com ID {tarefa_id} não encontrada"
        )
    
    return {"message": f"Tarefa {tarefa_id} deletada com sucesso"}

@router.get("/kanban/summary")
async def get_kanban_summary(db: Session = Depends(get_db)):
    """
    Retorna um resumo do Kanban com contagem de tarefas por status
    """
    service = TarefaService(db)
    
    summary = {
        "demanda": len(service.get_tarefas_by_status("demanda")),
        "a-fazer": len(service.get_tarefas_by_status("a-fazer")),
        "em-andamento": len(service.get_tarefas_by_status("em-andamento")),
        "erro": len(service.get_tarefas_by_status("erro")),
        "feito": len(service.get_tarefas_by_status("feito")),
        "total": len(service.get_all_tarefas())
    }
    
    return summary
